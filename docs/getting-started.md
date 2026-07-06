# Getting Started with Praxis

## Prerequisites

- Python 3.10+
- Ollama with `nomic-embed-text` model (for embeddings)
- Nellie-RS server (for AMP refinements)
- Claude or OpenAI API key

## Installation

```bash
git clone git@github.com:mmorris35/praxis.git
cd praxis
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running an Example

```bash
cd examples/cmmc-buddy

# Configure
export ANTHROPIC_API_KEY="your-key"
export OLLAMA_URL="http://localhost:11434"  # or your Ollama server
export NELLIE_URL="http://localhost:8765"   # or your Nellie server

# Ingest data
python -m core.ingest.ingest_full

# Run
uvicorn core.gateway.main:app --port 8081
```

## Creating a New Expert System

1. **Create example directory**
   ```bash
   mkdir -p examples/my-domain/data/structured
   mkdir -p examples/my-domain/ui
   mkdir -p examples/my-domain/config
   ```

2. **Gather foundation data (Layer 1)**
   - Find official structured data (JSON, XML, OSCAL)
   - Avoid PDFs if possible
   - One concept per chunk

3. **Build expert layer (Layer 2)**
   - Interview domain experts
   - Document practical procedures
   - Map theory to action
   - Include: what assessors want, common gaps, tips

4. **Create ingest script**
   - Parse your data format
   - Extract rich metadata
   - Load into ChromaDB with embeddings

5. **Configure and run**
   - Copy `core/config/gateway.yaml.template`
   - Set collection name, API keys
   - Run gateway

6. **Enable refinements**
   - Configure Nellie connection
   - Let real usage improve the system

## Connect a Coding Agent

Praxis exposes its knowledge base as an MCP server, so coding agents (Claude
Code, Cursor, etc.) can query grounded documentation instead of guessing at
API syntax.

### Local (stdio) — for a single editor

Start the MCP server as a subprocess of your editor:

```json
// .mcp.json (Claude Code) or equivalent
{
  "mcpServers": {
    "praxis": { "command": "praxis", "args": ["mcp", "stdio"] }
  }
}
```

### Shared instance (streamable-HTTP) — for a team

Run the server on a shared host:

```bash
praxis mcp http --port 8790
```

Then configure each editor to connect:

```json
{
  "mcpServers": {
    "praxis": { "type": "streamableHttp", "url": "http://your-host:8790/mcp" }
  }
}
```

### Available tools

- **`knowledge_search`** — Search the knowledge base. Returns ranked context
  passages with source attribution. Use this for compliance controls, API syntax,
  domain-specific documentation, and anything else indexed in Praxis.
  - `query` (str): Natural language search query.
  - `top_k` (int, optional): Number of results (1-25, default 10).

- **`list_domains`** — List the configured knowledge domain(s) so the agent
  knows what corpora are available.

### Note on transports

Praxis MCP supports **stdio** and **streamable-HTTP** only. SSE transport is
intentionally excluded due to connection stability issues in long-running agent
sessions.
