#!/usr/bin/env python3
"""Ingest remaining sources: M365 DSC and Azure Monitor/Sentinel."""
import os
import re
import sys
import time
from pathlib import Path

import chromadb
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.gateway.rag import LocalEmbeddingFunction

CHROMA_DIR = Path(__file__).parent.parent.parent / "examples" / "cmmc-buddy" / "data" / "chroma"


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


def ingest_dir(name, base_path, doc_paths, client, ef, extensions=None):
    if extensions is None:
        extensions = [".md"]
    all_chunks = []
    file_count = 0
    for doc_path in doc_paths:
        full = Path(base_path) / doc_path
        if not full.exists():
            print(f"  Path not found: {full}")
            continue
        for root, dirs, files in os.walk(full):
            for f in files:
                if any(f.endswith(ext) for ext in extensions):
                    fp = Path(root) / f
                    try:
                        content = fp.read_text(errors="ignore")
                        if len(content.strip()) > 50:
                            file_count += 1
                            rel = str(fp.relative_to(Path(base_path)))
                            for i, chunk in enumerate(chunk_text(content)):
                                cid = re.sub(r'[^a-zA-Z0-9_.-]', '_', f"{name}_{rel}_{i}")[:200]
                                all_chunks.append({"id": cid, "text": chunk, "source": name, "file": rel})
                    except Exception:
                        pass

    if not all_chunks:
        print(f"  No docs found for {name}")
        return 0

    print(f"  {name}: {file_count} files, {len(all_chunks)} chunks")
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
        print(f"    Indexed {min(i+bs, len(all_chunks))}/{len(all_chunks)}")
    return len(all_chunks)


def main():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = LocalEmbeddingFunction()
    total = 0
    start = time.time()

    # M365 DSC
    m365_base = "/tmp/praxis-m365dsc"
    if Path(m365_base).exists():
        print("=== M365 DSC ===")
        c = ingest_dir("m365-dsc", m365_base,
                       ["docs/docs", "Modules"],
                       client, ef)
        total += c

    # Azure Monitor / Sentinel
    az_base = "/tmp/praxis-azure-monitor"
    if Path(az_base).exists():
        print("=== Azure Monitor / Sentinel / KQL ===")
        c = ingest_dir("azure-monitor-sentinel", az_base,
                       ["articles/azure-monitor", "articles/sentinel",
                        "articles/data-explorer/kusto/query"],
                       client, ef)
        total += c
    else:
        print("Azure Monitor clone not ready yet, skipping")

    elapsed = time.time() - start
    print(f"\nDone: {total} chunks in {elapsed:.0f}s")

    # Smoke tests
    print("\n=== SMOKE TESTS ===")
    tests = [
        ("m365-dsc", "Microsoft365DSC export current tenant configuration"),
        ("azure-monitor-sentinel", "KQL query to find failed sign-in attempts"),
    ]
    for cname, q in tests:
        try:
            col = client.get_collection(cname, embedding_function=ef)
            r = col.query(query_texts=[q], n_results=3)
            print(f"\nQUERY [{cname}]: {q}")
            if r["ids"][0]:
                for i in range(min(3, len(r["ids"][0]))):
                    d = r["distances"][0][i]
                    doc = r["documents"][0][i][:150].replace("\n", " ")
                    print(f"  #{i+1} dist={d:.3f} | {doc}...")
                print("  PASS")
            else:
                print("  FAIL")
        except Exception as e:
            print(f"  SKIP: {e}")


if __name__ == "__main__":
    main()
