#!/usr/bin/env python3
"""Fetch Azure Monitor/Sentinel/KQL docs via GitHub API and ingest into Praxis."""
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import chromadb
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.gateway.rag import LocalEmbeddingFunction

CHROMA_DIR = Path(__file__).parent.parent.parent / "examples" / "cmmc-buddy" / "data" / "chroma"
SAVE_DIR = Path("/tmp/praxis-azure-fetched")

REPO = "MicrosoftDocs/azure-docs"
BRANCH = "main"
PATHS = [
    "articles/azure-monitor",
    "articles/sentinel",
    "articles/data-explorer/kusto/query",
]

API_BASE = "https://api.github.com"


def get_tree(path):
    """Get file tree for a path via GitHub API."""
    url = f"{API_BASE}/repos/{REPO}/contents/{path}?ref={BRANCH}"
    req = Request(url, headers={"Accept": "application/vnd.github.v3+json"})
    try:
        resp = urlopen(req, timeout=30)
        return json.loads(resp.read())
    except HTTPError as e:
        print(f"  API error for {path}: {e.code}")
        return []


def fetch_file(download_url):
    """Download a file's content."""
    try:
        req = Request(download_url, headers={"Accept": "text/plain"})
        resp = urlopen(req, timeout=30)
        return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return None


def walk_github_tree(path, depth=0):
    """Recursively walk a GitHub directory tree and yield (path, download_url) for .md files."""
    if depth > 5:
        return
    items = get_tree(path)
    if not isinstance(items, list):
        return
    for item in items:
        if item["type"] == "file" and item["name"].endswith(".md"):
            yield item["path"], item.get("download_url", "")
        elif item["type"] == "dir":
            time.sleep(0.1)  # rate limit
            yield from walk_github_tree(item["path"], depth + 1)


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
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    name = "azure-monitor-sentinel"

    print(f"Fetching Azure Monitor/Sentinel/KQL docs via GitHub API")
    print(f"This will take a few minutes due to API rate limits...")

    all_chunks = []
    file_count = 0

    for base_path in PATHS:
        print(f"\nScanning: {base_path}")
        for fpath, dl_url in walk_github_tree(base_path):
            if not dl_url:
                continue
            content = fetch_file(dl_url)
            if not content or len(content.strip()) < 50:
                continue
            file_count += 1
            for i, chunk in enumerate(chunk_text(content)):
                cid = re.sub(r'[^a-zA-Z0-9_.-]', '_', f"{name}_{fpath}_{i}")[:200]
                all_chunks.append({"id": cid, "text": chunk, "source": name, "file": fpath})
            if file_count % 50 == 0:
                print(f"  Fetched {file_count} files, {len(all_chunks)} chunks so far...")
            time.sleep(0.05)  # gentle rate limit

    print(f"\nTotal: {file_count} files, {len(all_chunks)} chunks")

    if not all_chunks:
        print("No docs fetched!")
        return

    # Ingest
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = LocalEmbeddingFunction()

    try:
        client.delete_collection(name)
    except Exception:
        pass

    col = client.create_collection(name=name, embedding_function=ef)
    bs = 500
    for i in range(0, len(all_chunks), bs):
        batch = all_chunks[i:i+bs]
        col.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[{"source": c["source"], "file": c["file"]} for c in batch],
        )
        print(f"  Indexed {min(i+bs, len(all_chunks))}/{len(all_chunks)}")

    print(f"\nDone: {len(all_chunks)} chunks in '{name}'")

    # Smoke test
    print("\n=== SMOKE TESTS ===")
    queries = [
        "KQL query to find failed sign-in attempts",
        "Azure Monitor alert rule configuration",
        "Microsoft Sentinel playbook automation",
        "Log Analytics workspace data retention",
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
