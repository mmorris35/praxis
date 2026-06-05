# Verification Report: Praxis Wiki Mode

## Summary
- **Status**: PARTIAL
- **Features Verified**: 6/7
- **Critical Issues**: 2
- **Warnings**: 5
- **Observations**: 3

---

## Smoke Tests

| Test | Result | Notes |
|------|--------|-------|
| `pytest tests/wiki/ -v` | PASS | 31/31 tests pass |
| `python praxis_cli.py --version` | PASS | `praxis, version 0.1.0` |
| `python praxis_cli.py wiki --help` | PASS | Shows all 4 subcommands |
| `wiki generate --help` | PASS | Shows all options incl. `--no-feedback` |
| `wiki update --help` | PASS | |
| `wiki serve --help` | PASS | |
| `wiki export --help` | PASS | |
| All module imports (`core.wiki.*`) | PASS | All 8 modules import cleanly |

---

## Feature Verification

### Feature 1: Agent-driven wiki page generation from ChromaDB knowledge chunks
**Status: PASS**

`WikiGenerator` in `core/wiki/generator.py` implements the full pipeline:
- `extract_chunks()` fetches all docs from ChromaDB in batches of 1000
- `cluster_concepts()` groups chunks by `control_id` (primary) or `source` (fallback)
- `generate_page()` calls Anthropic `claude-sonnet-4-20250514` with a structured distillation prompt
- `generate_all()` orchestrates the pipeline with per-page error handling (failed pages are skipped, not fatal)

Empty ChromaDB is handled correctly — `generate_all()` returns `[]` early.

### Feature 2: Automatic interlinking with [[wikilinks]] across concept pages
**Status: PASS with Warning**

`WikiInterlinker` in `core/wiki/interlinker.py` builds a concept index and injects `[[Title]]` links into page content. Reverse links (`linked_from`) are correctly computed in `interlink_all()`. Self-links are prevented.

**Warning**: The alias-building code on line 24 uses `rstrip("policy")` which is treated as a character set, not a suffix string. `"Continuity".lower().rstrip("policy")` becomes `"continuit"` (strips trailing `y`). `"Privacy Policy"` becomes `"privac"`. This produces corrupted aliases for any title ending in the characters `{p,o,l,i,c,y}`. The intent was to strip the literal suffix ` policy` — use `removesuffix(" policy")` instead.

The bug does not break interlinking itself but creates spurious short-string aliases in the concept index that could cause false positive matches (e.g., `"ac-1"` matching anywhere the substring appears).

### Feature 3: Three-layer visibility annotations (Foundation/Institutional/Refinement)
**Status: PARTIAL**

Layer tracking is implemented: chunks carry a `layer` metadata field, clusters track `layer_sources`, and pages carry a `layers` list. The LLM prompt requests a `## Layer Origins` section in generated content. The index page renders layer badges as inline code (e.g., `` `foundation` `` `` `refinement` ``).

**Gap 1**: Layer annotations do not appear in individual concept page files (`concepts/<slug>.md`). `WikiWriter.write_page()` writes `page.content` directly — it is the LLM's responsibility to include the `## Layer Origins` section. There is no fallback frontmatter or header injected by the writer. If the LLM omits the section, pages have no layer annotation.

**Gap 2**: The code treats layer values as arbitrary strings from ChromaDB metadata. The `institutional` layer (one of the three named in the specification) is never explicitly handled, validated, or mentioned in the wiki codebase. The test fixtures use only `foundation` and `refinement`. If `institutional` chunks exist in ChromaDB they will work, but there is no explicit support or test coverage.

### Feature 4: Incremental updates when new refinements land
**Status: FAIL — Critical Bug**

`IncrementalUpdater.detect_changes()` in `core/wiki/incremental.py` (line 35) reads `chunk_ids` from each page entry in `generation-log.json` to build the set of previously-seen chunk IDs.

`WikiWriter.write_generation_log()` in `core/wiki/writer.py` (lines 50-60) saves `chunk_count` (an integer) but **does not save `chunk_ids`** (the list of IDs). The key `chunk_ids` is never written to the log.

**Impact**: On every `praxis wiki update` run, `last_chunk_ids` is always an empty set. Every chunk in the current ChromaDB appears as `new`, and every concept page is flagged as `affected`. The `update` command always regenerates all pages — equivalent behavior to `generate`, but without re-running interlinking, graph updates, or feedback ingestion. The feature does not work as specified.

**The tests pass because** the incremental tests mock `_load_last_generation` and `cluster_concepts` directly; they never exercise the real `write_generation_log` + `detect_changes` round-trip.

**Fix**: Add `"chunk_ids": p.chunk_ids` to the per-page dict in `write_generation_log`.

### Feature 5: Knowledge graph metadata (graph.json, link-map.json)
**Status: PASS**

`KnowledgeGraph` in `core/wiki/graph.py` produces:
- `wiki/graph.json` — nodes (id, label, layers, chunk_count) and edges (source, target)
- `wiki/_meta/link-map.json` — per-slug entry with links_to, linked_from, and link_count

Both files are written correctly. Tests verify both outputs.

### Feature 6: Bidirectional RAG integration — wiki pages feed back into ChromaDB
**Status: PASS with Warning**

`WikiFeedback` in `core/wiki/feedback.py` upserts wiki pages into ChromaDB with `source: "wiki"` and `layer: "wiki-generated"` metadata. Stale pages (slugs no longer generated) are deleted via `remove_stale()`.

`WikiGenerator.generate` CLI command calls `fb.ingest_pages(pages)` and `fb.remove_stale(...)` after generation unless `--no-feedback` is set.

**Warning**: There are zero tests for `WikiFeedback`. No `tests/wiki/test_feedback.py` file exists. The feedback path (the only path that writes back to ChromaDB) is entirely untested.

### Feature 7: CLI commands — generate, update, serve, export
**Status: PASS with Warnings**

All four commands are implemented and reachable. Help text is complete.

**Warning 1 — HTML export is not implemented**: `export --format html` accepts the option but performs an identical directory copy as `--format markdown`. No markdown-to-HTML conversion occurs. The format flag is cosmetic.

**Warning 2 — `serve` is not functionally tested**: `test_cli.py` only checks that "serve" appears in `--help` output. The actual serving behavior (correct directory, missing wiki dir error) is untested.

**Warning 3 — Incremental `update` does not refresh interlinking or graph**: After regenerating affected pages, `IncrementalUpdater.update()` writes raw page content without re-running `WikiInterlinker`. New/updated pages will lack wikilinks to recently-added concepts, and the knowledge graph files are not updated. This is a design incompleteness.

---

## Edge Cases & Code Quality

### Path Traversal in writer.py
`WikiWriter.write_page()` constructs output path as `concepts_dir / f"{page.slug}.md"`. A slug like `../../../tmp/evil` would resolve outside the wiki directory.

**In practice, this is mitigated**: slugs are generated via `python-slugify` which strips `/` and `.` characters — `../../../etc/passwd` → `etc-passwd`. However, there is no explicit path validation in `write_page()`. If a slug were ever constructed without going through `slugify()` (e.g., from `IncrementalUpdater.update()` line 75 which uses `cluster.slug` directly from the generator), the protection depends entirely on `slugify` being called upstream.

Recommendation: Add a `Path.resolve()` check in `write_page()` to assert the resolved path stays under `concepts_dir`.

### Destructive `shutil.rmtree` in export command
`export_wiki` (cli.py line 136) unconditionally calls `shutil.rmtree(dst)` if the destination exists. A user invoking `praxis wiki export -o /` or `praxis wiki export -o ~` would delete their home directory. The CLI has no guard against this.

### OllamaEmbeddingFunction Default URL
`OllamaEmbeddingFunction.__init__` defaults `base_url` to `"http://100.87.147.89:11434"` (a hardcoded IP). This default is never used in the wiki path (generator and feedback always pass `config.ollama_url`, which defaults to `localhost`), but it is a landmine for anyone instantiating the class directly or reusing it from the gateway.

### `pass` in cli.py
The `pass` on line 10 is the body of the `wiki()` Click group function — this is correct Click idiom and not a stub.

### `chunk_ids` never saved in generation log
See Feature 4 above. This is the most impactful code defect found.

### Missing `chunk_ids` test coverage
`test_write_generation_log` in `test_generator.py` verifies `total_pages` and `slug` but does not assert that `chunk_ids` is present in log entries. Had this assertion existed, the bug would have been caught.

---

## Issues Found

### Critical (must fix)

**C1 — Incremental update broken: `chunk_ids` not saved in generation log**
- File: `core/wiki/writer.py`, `write_generation_log()` lines 50–60
- Root cause: `chunk_count` (int) is saved instead of `chunk_ids` (list of strings)
- Impact: `praxis wiki update` always considers all chunks new, regenerates all pages on every run, defeating the purpose of incremental updates
- Fix: Change `"chunk_count": len(p.chunk_ids)` to `"chunk_ids": p.chunk_ids` (and optionally also save `chunk_count` for humans)

**C2 — Destructive export with no path guard**
- File: `core/wiki/cli.py`, `export_wiki()` line 136
- Root cause: `shutil.rmtree(dst)` on any user-supplied `--output` path with no validation
- Impact: `praxis wiki export -o ~` deletes the user's home directory
- Fix: Validate that `dst` is not a filesystem root, home directory, or parent of the wiki source; or at minimum require a confirmation flag when the path already exists

### Warnings (should fix)

**W1 — `rstrip("policy")` treats argument as char set, not suffix string**
- File: `core/wiki/interlinker.py`, line 24
- Impact: Corrupts aliases for titles ending in any of `{p,o,l,i,c,y}` — e.g., `"Continuity"` → `"continuit"`, `"Privacy Policy"` → `"privac"`
- Fix: `page.title.lower().removesuffix(" policy").strip()`

**W2 — HTML export not implemented**
- File: `core/wiki/cli.py`, `export_wiki()`
- Impact: `--format html` silently exports markdown files with an HTML claim in output message; misleads users
- Fix: Either implement markdown-to-HTML conversion (e.g., via `markdown` or `mistune`) or remove the `html` choice from the option and document markdown-only export

**W3 — No tests for `WikiFeedback`**
- File: `core/wiki/feedback.py`; no corresponding test file
- Impact: The only code path that mutates ChromaDB (the bidirectional RAG feedback loop) is completely untested. Regressions will not be caught.
- Fix: Add `tests/wiki/test_feedback.py` with mocked ChromaDB covering `ingest_pages` and `remove_stale`

**W4 — Incremental update does not re-interlink or update graph**
- File: `core/wiki/incremental.py`, `update()`
- Impact: After updating affected pages, wikilinks in updated pages are not refreshed, and `graph.json`/`link-map.json` are stale
- Fix: After regenerating pages, run `WikiInterlinker` on the full page set and rewrite the graph files

**W5 — `serve` command has no functional tests**
- File: `tests/wiki/test_cli.py`
- Impact: Missing-wiki-dir error path and server startup are untested
- Fix: Add tests for `serve --wiki-dir /nonexistent` (should print error, exit 0) and verify it does not raise on valid paths

### Observations (nice to have)

**O1 — `institutional` layer not explicitly handled or tested**
The specification names three layers: Foundation, Institutional, Refinement. The code treats layer values as opaque strings. Fixtures only cover `foundation` and `refinement`. Adding an explicit validation or enum would make the three-layer contract explicit.

**O2 — LLM model string could become stale**
`WikiConfig.llm_model` defaults to `"claude-sonnet-4-20250514"`. This is a valid model ID in the installed SDK (0.105.2) but will silently fail if the model is retired. Consider making this an env-var override with a documented default.

**O3 — Layer annotations only appear in index.md, not in concept pages**
Individual `concepts/<slug>.md` files have no guaranteed layer annotation. The LLM is prompted to include a `## Layer Origins` section, but there is no writer-level enforcement. A frontmatter block (e.g., YAML with `layers:`) written by `WikiWriter.write_page()` would make annotations reliable and machine-parseable.

---

## Recommendations

1. **Fix C1 immediately** before any production use — incremental updates are completely non-functional due to the `chunk_ids` vs `chunk_count` bug in `write_generation_log`. This is a one-line fix.

2. **Fix C2 (export rmtree guard)** — low effort, high blast-radius if triggered accidentally.

3. **Add `test_feedback.py`** — the feedback module is the most operationally risky code (mutates the primary RAG store) and has zero test coverage.

4. **Fix W1 (`rstrip` → `removesuffix`)** — silent data corruption in alias generation; easy fix.

5. **Decide on HTML export** — either implement it or remove the option to avoid silent misleading behavior.

6. **Add a round-trip integration test** for incremental updates that exercises the real `write_generation_log` → `detect_changes` path to prevent regression of C1.
