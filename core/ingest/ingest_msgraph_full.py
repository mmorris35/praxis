#!/usr/bin/env python3
"""Full Microsoft Graph API + PowerShell cmdlet docs ingest for Praxis."""
import os
import re
import sys
import time
import chromadb
from pathlib import Path

sys.path.insert(0, str(Path.home() / "github" / "praxis"))
from core.gateway.rag import LocalEmbeddingFunction

GRAPH_DOCS = Path("/tmp/microsoft-graph-docs-contrib")
PS_DOCS = Path("/tmp/msgraph-sdk-powershell")
PRAXIS = Path.home() / "github" / "praxis"
CHROMA_DIR = PRAXIS / "examples" / "cmmc-buddy" / "data" / "chroma"

MAX_CHUNK = 2000
BATCH_SIZE = 500


def extract_service_area(filepath):
    name = filepath.stem
    parts = name.split("-")
    return parts[0] if parts else "unknown"


def extract_http_method(content):
    m = re.search(r'```http\s*\n(GET|POST|PUT|PATCH|DELETE)\s', content)
    return m.group(1) if m else ""


def extract_title(content):
    fm = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if fm:
        tm = re.search(r'title:\s*["\']?(.+?)["\']?\s*$', fm.group(1), re.MULTILINE)
        if tm:
            return tm.group(1).strip('"\'  ')
    hm = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if hm:
        return hm.group(1).strip()
    return ""


def strip_frontmatter(content):
    return re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)


def strip_html_comments(content):
    return re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)


def strip_includes(content):
    return re.sub(r'\[!INCLUDE\s+\[.*?\]\(.*?\)\]', '', content)


def chunk_markdown(content, max_size=MAX_CHUNK):
    content = strip_frontmatter(content)
    content = strip_html_comments(content)
    content = strip_includes(content)
    content = content.strip()

    if not content or len(content) < 50:
        return []

    if len(content) <= max_size:
        return [content]

    sections = re.split(r'(?=^## )', content, flags=re.MULTILINE)
    chunks = []
    current = ""

    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(current) + len(section) + 2 <= max_size:
            current = (current + "\n\n" + section).strip()
        else:
            if current:
                chunks.append(current)
            if len(section) > max_size:
                subsections = re.split(r'(?=^### )', section, flags=re.MULTILINE)
                sub_current = ""
                for sub in subsections:
                    sub = sub.strip()
                    if not sub:
                        continue
                    if len(sub_current) + len(sub) + 2 <= max_size:
                        sub_current = (sub_current + "\n\n" + sub).strip()
                    else:
                        if sub_current:
                            chunks.append(sub_current)
                        if len(sub) > max_size:
                            chunks.append(sub[:max_size])
                        else:
                            sub_current = sub
                if sub_current:
                    chunks.append(sub_current)
                current = ""
            else:
                current = section

    if current:
        chunks.append(current)

    return [c for c in chunks if len(c) >= 50]


def process_graph_api_docs(api_dir, version):
    results = []
    md_files = sorted(api_dir.glob("*.md"))
    for f in md_files:
        try:
            content = f.read_text(errors="replace")
        except Exception:
            continue

        title = extract_title(content)
        service = extract_service_area(f)
        method = extract_http_method(content)

        chunks = chunk_markdown(content)
        for i, chunk in enumerate(chunks):
            chunk_id = "graph-%s-%s" % (version, f.stem)
            if len(chunks) > 1:
                chunk_id += "-%d" % i
            results.append({
                "id": chunk_id,
                "text": chunk,
                "metadata": {
                    "source": "msgraph-%s" % version,
                    "service": service,
                    "title": title[:200] if title else f.stem,
                    "http_method": method,
                    "doc_type": "api-reference",
                    "filename": f.name,
                }
            })

    return results


def process_powershell_docs(ps_src):
    results = []
    for f in sorted(ps_src.rglob("*.md")):
        if f.name.lower() in ("readme.md", "how-to.md"):
            continue

        try:
            content = f.read_text(errors="replace")
        except Exception:
            continue

        if len(content) < 50:
            continue

        rel = f.relative_to(ps_src)
        parts = list(rel.parts)
        module = parts[0] if parts else "unknown"
        version = ""
        for p in parts:
            if p in ("v1.0", "beta"):
                version = p
                break

        cmdlet_name = f.stem
        chunks = chunk_markdown(content)
        for i, chunk in enumerate(chunks):
            chunk_id = "ps-%s-%s-%s" % (version or "v1.0", module, cmdlet_name)
            if len(chunks) > 1:
                chunk_id += "-%d" % i
            results.append({
                "id": chunk_id,
                "text": chunk,
                "metadata": {
                    "source": "powershell-%s" % (version or "v1.0"),
                    "service": module,
                    "title": cmdlet_name,
                    "http_method": "",
                    "doc_type": "powershell-cmdlet",
                    "filename": f.name,
                }
            })

    return results


def main():
    start = time.time()

    print("=" * 60)
    print("Microsoft Graph API + PowerShell Full Ingest")
    print("=" * 60)

    all_chunks = []

    # Graph API v1.0
    v1_api = GRAPH_DOCS / "api-reference" / "v1.0" / "api"
    if v1_api.exists():
        print("\nProcessing Graph API v1.0...")
        v1_chunks = process_graph_api_docs(v1_api, "v1.0")
        print("  %d chunks from v1.0 (%d files)" % (len(v1_chunks), len(list(v1_api.glob("*.md")))))
        all_chunks.extend(v1_chunks)

    # Graph API beta
    beta_api = GRAPH_DOCS / "api-reference" / "beta" / "api"
    if beta_api.exists():
        print("\nProcessing Graph API beta...")
        beta_chunks = process_graph_api_docs(beta_api, "beta")
        print("  %d chunks from beta (%d files)" % (len(beta_chunks), len(list(beta_api.glob("*.md")))))
        all_chunks.extend(beta_chunks)

    # Graph concepts
    concepts = GRAPH_DOCS / "concepts"
    if concepts.exists():
        print("\nProcessing Graph concepts...")
        concept_chunks = []
        for f in sorted(concepts.rglob("*.md")):
            try:
                content = f.read_text(errors="replace")
            except Exception:
                continue
            title = extract_title(content)
            chunks = chunk_markdown(content)
            for i, chunk in enumerate(chunks):
                chunk_id = "graph-concept-%s" % f.stem
                if len(chunks) > 1:
                    chunk_id += "-%d" % i
                concept_chunks.append({
                    "id": chunk_id,
                    "text": chunk,
                    "metadata": {
                        "source": "msgraph-concepts",
                        "service": "concepts",
                        "title": title[:200] if title else f.stem,
                        "http_method": "",
                        "doc_type": "concept",
                        "filename": f.name,
                    }
                })
        print("  %d chunks from concepts" % len(concept_chunks))
        all_chunks.extend(concept_chunks)

    # PowerShell docs
    ps_src = PS_DOCS / "src"
    if ps_src.exists():
        print("\nProcessing PowerShell cmdlet docs...")
        ps_chunks = process_powershell_docs(ps_src)
        print("  %d chunks from PowerShell" % len(ps_chunks))
        all_chunks.extend(ps_chunks)

    print("\nTotal: %d chunks" % len(all_chunks))

    # Deduplicate
    seen = set()
    deduped = []
    for c in all_chunks:
        if c["id"] not in seen:
            seen.add(c["id"])
            deduped.append(c)
    all_chunks = deduped
    print("After dedup: %d chunks" % len(all_chunks))

    # ChromaDB setup
    print("\nSetting up ChromaDB at %s..." % CHROMA_DIR)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    for old_name in ("msgraph-docs", "msgraph-api-full"):
        try:
            client.delete_collection(old_name)
            print("  Deleted old %s collection" % old_name)
        except Exception:
            pass

    ef = LocalEmbeddingFunction()
    collection = client.create_collection(name="msgraph-api-full", embedding_function=ef)
    print("  Created msgraph-api-full collection")

    # Ingest
    print("\nIngesting %d chunks in batches of %d..." % (len(all_chunks), BATCH_SIZE))
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i:i+BATCH_SIZE]
        collection.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )
        elapsed = time.time() - start
        done = i + len(batch)
        print("  Batch %d: %d indexed (total %d/%d, %.0fs elapsed)" % (
            i // BATCH_SIZE + 1, len(batch), done, len(all_chunks), elapsed))

    elapsed = time.time() - start
    print("\nDone! %d chunks indexed in %.0fs" % (len(all_chunks), elapsed))
    print("Collections: %s" % [c.name for c in client.list_collections()])

    return len(all_chunks)


if __name__ == "__main__":
    main()
