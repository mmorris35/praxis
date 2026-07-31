#!/usr/bin/env python3
"""Ingest Azure Monitor + KQL docs from their dedicated repos into Praxis."""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import chromadb
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.gateway.rag import LocalEmbeddingFunction

CHROMA_DIR = Path(__file__).parent.parent.parent / "examples" / "cmmc-buddy" / "data" / "chroma"
WORK_DIR = Path("/tmp/praxis-azure-ingest2")

REPOS = [
    {
        "repo": "https://github.com/MicrosoftDocs/azure-monitor-docs.git",
        "doc_paths": ["articles/azure-monitor", "articles/advisor", "articles/operations", "articles/service-health"],
        "label": "Azure Monitor",
    },
    {
        "repo": "https://github.com/MicrosoftDocs/dataexplorer-docs.git",
        "doc_paths": ["data-explorer/kusto/query", "data-explorer/kusto/functions-library", "data-explorer/kusto/management"],
        "label": "KQL / Data Explorer",
    },
]

COLLECTION_NAME = "azure-monitor-sentinel"


def chunk_text(text, max_size=2000):
    chunks = []
    sections = re.split(r'(?=^#{1,3}\s)', text, flags=re.MULTILINE)
    current = ""
    for section in sections:
        if not section.strip():
            continue
        if len(current) + len(section) <= max_size:
            current += section
        else:
            if current.strip():
                chunks.append(current.strip())
            if len(section) > max_size:
                parts = re.split(r'\n\n(?!```)', section)
                sub = ""
                for part in parts:
                    if len(sub) + len(part) <= max_size:
                        sub += "\n\n" + part
                    else:
                        if sub.strip():
                            chunks.append(sub.strip())
                        sub = part
                if sub.strip():
                    chunks.append(sub.strip())
                current = ""
            else:
                current = section
    if current.strip():
        chunks.append(current.strip())
    return chunks if chunks else [text[:max_size]]


def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    all_chunks = []
    total_files = 0

    for repo_info in REPOS:
        repo_url = repo_info["repo"]
        label = repo_info["label"]
        dest = WORK_DIR / label.replace(" ", "_").replace("/", "_")

        print(f"\n=== {label} ===")
        print(f"Cloning {repo_url}...")

        if dest.exists():
            subprocess.run(["rm", "-rf", str(dest)])

        r = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(dest)],
            capture_output=True, timeout=180,
        )
        if r.returncode != 0:
            print(f"  Clone failed: {r.stderr.decode()[:200]}")
            continue

        for doc_path in repo_info["doc_paths"]:
            full = dest / doc_path
            if not full.exists():
                # Try without leading directory
                alt_paths = list(dest.glob(f"**/{doc_path.split('/')[-1]}"))
                if alt_paths:
                    full = alt_paths[0]
                else:
                    print(f"  Path not found: {doc_path}")
                    continue

            file_count = 0
            for root, dirs, files in os.walk(full):
                for f in files:
                    if f.endswith(".md"):
                        fp = Path(root) / f
                        try:
                            content = fp.read_text(errors="ignore")
                            if len(content.strip()) > 50:
                                file_count += 1
                                total_files += 1
                                rel = str(fp.relative_to(dest))
                                for i, chunk in enumerate(chunk_text(content)):
                                    cid = re.sub(r'[^a-zA-Z0-9_.-]', '_',
                                                 f"azmon_{rel}_{i}")[:200]
                                    all_chunks.append({
                                        "id": cid,
                                        "text": chunk,
                                        "source": COLLECTION_NAME,
                                        "file": rel,
                                    })
                        except Exception:
                            pass
            print(f"  {doc_path}: {file_count} files")

        subprocess.run(["rm", "-rf", str(dest)])

    print(f"\nTotal: {total_files} files, {len(all_chunks)} chunks")

    if not all_chunks:
        print("Nothing to ingest!")
        return

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = LocalEmbeddingFunction()

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    col = client.create_collection(name=COLLECTION_NAME, embedding_function=ef)

    bs = 500
    for i in range(0, len(all_chunks), bs):
        batch = all_chunks[i:i+bs]
        col.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[{"source": c["source"], "file": c["file"]} for c in batch],
        )
        print(f"  Indexed {min(i+bs, len(all_chunks))}/{len(all_chunks)}")

    print(f"\nDone: {len(all_chunks)} chunks in '{COLLECTION_NAME}'")

    # Smoke tests
    print("\n=== SMOKE TESTS ===")
    queries = [
        "KQL query to find failed sign-in attempts",
        "Azure Monitor alert rule configuration",
        "Log Analytics workspace data retention",
        "KQL summarize operator examples",
    ]
    for q in queries:
        r = col.query(query_texts=[q], n_results=3)
        print(f"\nQUERY: {q}")
        for i in range(min(3, len(r["ids"][0]))):
            d = r["distances"][0][i]
            doc = r["documents"][0][i][:150].replace("\n", " ")
            print(f"  #{i+1} dist={d:.3f} | {doc}...")
        print("  PASS" if r["ids"][0] else "  FAIL")


if __name__ == "__main__":
    main()
