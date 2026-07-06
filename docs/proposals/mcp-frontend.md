# Proposal: MCP Server Front-End for Praxis

**Status:** Draft for review
**Author:** Nagatha (drafted for SDS-Mike)
**Intended implementer:** Bilby
**Related:** `core/gateway/rag.py`, `core/gateway/main.py`, `praxis_cli.py`

## Summary

Add a Model Context Protocol (MCP) server to Praxis that exposes the existing
RAG retrieval layer as a **tool a coding agent can call** (Claude Code, Cursor,
etc.). Today Praxis surfaces its knowledge only through the human-facing FastAPI
chat gateway (`core/gateway/main.py`). This proposal adds a second, read-only
consumption path so a coding agent can pull grounded, version-accurate
documentation directly into its context while it works.

## Motivation

The concrete driver: while writing Microsoft Graph API calls, coding agents
routinely guess at `$filter` / `$select` / `$expand` syntax, swallow Graph error
bodies, and misreport an empty result as "no data on the other end." The fix is
to put authoritative docs in the agent's toolbelt so it queries them instead of
guessing.

Praxis already does the hard part — chunking, embedding (Ollama /
`nomic-embed-text`), hybrid retrieval, and source attribution. What it lacks is
an MCP endpoint. Adding one:

- Solves the Graph-syntax problem (index the Graph docs as a Praxis domain, then
  query them from the editor).
- Upgrades Praxis from "end-user chat app" to "also a developer knowledge
  source" — a genuine product feature, reusable for every domain (CMMC, mortgage,
  etc.), not just Graph.
- Keeps everything in-house (sequel-data IP) rather than depending on a
  third-party doc server.

## Goals

- Expose Praxis retrieval over MCP as a small set of read-only tools.
- Support **stdio** (local editor) and **streamable-HTTP** (shared instance)
  transports.
- Reuse `core/gateway/rag.py` verbatim — no reimplementation of retrieval.
- Ship a `praxis mcp` CLI subcommand so it starts the same way as the rest of
  the tooling.

## Non-Goals

- No write/ingest operations over MCP (indexing stays CLI/script-driven).
- **No SSE transport.** Our fleet has repeatedly hit SSE connection drops and
  session freezes (Nellie and Beer Can both moved off SSE). MCP-over-SSE is
  explicitly excluded; use stdio or streamable-HTTP only.
- No change to the existing human chat gateway.

## Design

### New module: `core/mcp/`

```
core/mcp/
  __init__.py
  server.py      # MCP server definition + tool registration
```

Recommended library: **FastMCP** (Python). It provides both stdio and
streamable-HTTP transports with a decorator-based tool API, so `server.py` stays
thin. Pin it to an exact version (see Dependencies).

### Tools

**`knowledge_search`** — the primary tool.

- Input: `query: str`, optional `top_k: int` (default from `gateway.yaml` →
  `rag.top_k`), optional `domain: str` (reserved for multi-collection setups).
- Behavior: call `rag.retrieve(query, top_k=top_k)`, then return both the
  formatted context and structured sources:
  - `context`: `rag.format_context(chunks)`
  - `sources`: `rag.extract_sources(chunks)`
- Output: a single text block (formatted context) plus the sources list, so the
  agent gets citable references, not just prose.

**`list_domains`** (optional, nice-to-have) — return the configured
collection(s) so the agent knows what corpora are available.

Retrieval is already implemented and returns ranked chunk dicts with
`text`, `source`, `section`, `control_id`, `control_title`, `distance`. The MCP
layer is a thin adapter over these three existing functions:

```python
from gateway.rag import retrieve, format_context, extract_sources

def knowledge_search(query: str, top_k: int | None = None) -> dict:
    chunks = retrieve(query, top_k=top_k)
    return {
        "context": format_context(chunks),
        "sources": extract_sources(chunks),
    }
```

### CLI integration

Add an `mcp` command group to `praxis_cli.py` alongside `wiki`:

```
praxis mcp stdio                 # for a local editor (Claude Code)
praxis mcp http --port 8790      # streamable-HTTP for a shared instance
```

### Configuration

Reuse `config/gateway.yaml`. The MCP server reads the same `rag` block
(`chroma_path`, `collection`, `top_k`) via `rag._load_config()`. No new config
file. (Note for implementer: `OllamaEmbeddingFunction` currently hardcodes the
Ollama base URL in `rag.py` — out of scope here, but worth a follow-up to make
it config-driven.)

## Client configuration (what the end result looks like)

Local (stdio), e.g. Claude Code `.mcp.json`:

```json
{
  "mcpServers": {
    "praxis": { "command": "praxis", "args": ["mcp", "stdio"] }
  }
}
```

Shared instance (streamable-HTTP):

```json
{
  "mcpServers": {
    "praxis": { "type": "streamableHttp", "url": "http://mini-dev-server:8790/mcp" }
  }
}
```

## Security

- **Read-only.** No tool mutates the store or the filesystem.
- Cap `query` length and `top_k` (e.g. `top_k` ≤ 25) to bound work.
- The human chat gateway's prompt-injection filtering exists to protect an
  LLM answering untrusted public input. The MCP consumer is a trusted local
  agent, so heavy injection filtering is unnecessary here — but do not log raw
  queries to the security log path used by the gateway.

## Dependencies

Add exactly one new pinned dependency (FastMCP). Per house rules, pin the exact
version with `==` and do not use `>=`:

```
fastmcp==<latest-stable-at-implementation-time>
```

Implementer: check the current stable FastMCP version on PyPI and any recent
advisories before pinning. (Separately, `requirements.txt` currently uses `>=`
throughout — tightening those to exact pins is a worthwhile follow-up but is out
of scope for this PR.)

## Task breakdown (for the implementer)

- [ ] Add `core/mcp/server.py` with a FastMCP server exposing `knowledge_search`.
- [ ] Adapter reuses `gateway.rag.retrieve/format_context/extract_sources` — no
      new retrieval logic.
- [ ] Add `praxis mcp stdio` and `praxis mcp http --port` subcommands to
      `praxis_cli.py`.
- [ ] Enforce `top_k` cap and query-length cap.
- [ ] Pin `fastmcp==X.Y.Z` in `requirements.txt` (exact version).
- [ ] Docs: add a "Connect a coding agent" section to `docs/getting-started.md`
      with the stdio + streamable-HTTP client snippets above.
- [ ] (Optional) `list_domains` tool.
- [ ] (Follow-up, separate PR) Make the Ollama base URL in `rag.py`
      config-driven.

## Acceptance criteria

1. `praxis mcp stdio` starts a working MCP server; a local Claude Code session
   configured against it can call `knowledge_search` and receive ranked context
   plus sources from the active Chroma collection.
2. `praxis mcp http --port 8790` serves streamable-HTTP at `/mcp` and a client
   configured with `type: streamableHttp` can call the same tool.
3. **No SSE transport is exposed.**
4. No retrieval logic is duplicated — the MCP layer imports from
   `gateway.rag`.
5. A short manual eval passes: with a Graph-docs collection loaded, asking for a
   specific `$filter` example returns the documented syntax with a source
   reference (not a guess).

## Follow-ups (out of scope)

- Index the Microsoft Graph REST docs
  (`microsoftgraph/microsoft-graph-docs-contrib`, Markdown) as a Praxis domain so
  this MCP server can answer Graph questions.
- Multi-collection / domain routing if more than one corpus is served at once.
