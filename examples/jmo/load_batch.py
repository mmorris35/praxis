#!/usr/bin/env python3
"""Load chunks into ChromaDB one PDF at a time to avoid OOM."""

import sys
import json
import chromadb
from pathlib import Path
from extract_and_load import extract_pages, chunk_pages, SOURCES, PDF_DIR

CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma"

def load_one(pdf_name: str, meta: dict, offset: int):
    pdf_path = PDF_DIR / pdf_name
    if not pdf_path.exists():
        print(f"⚠ {pdf_name} not found")
        return 0

    print(f"📄 {meta['name']}")
    pages = extract_pages(pdf_path)
    print(f"   {len(pages)} pages extracted")

    chunks = chunk_pages(pages, meta)
    print(f"   {len(chunks)} chunks created")

    # Show section distribution
    sections = {}
    for c in chunks:
        s = c["section"]
        sections[s] = sections.get(s, 0) + 1
    print(f"   {len(sections)} unique sections")
    for s, count in sorted(sections.items(), key=lambda x: -x[1])[:8]:
        print(f"     {s}: {count}")

    # Load into ChromaDB in small batches
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    col = client.get_or_create_collection("guidelines")

    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        col.add(
            ids=[f"chunk_{offset + i + j}" for j in range(len(batch))],
            documents=[c["text"] for c in batch],
            metadatas=[{
                "source": c["source"],
                "agency": c["agency"],
                "short": c["short"],
                "section": c["section"],
                "start_page": c["start_page"],
                "end_page": c["end_page"],
            } for c in batch],
        )
        print(f"   Loaded {min(i + batch_size, len(chunks))}/{len(chunks)}")

    print(f"   ✅ Total in collection: {col.count()}")
    return len(chunks)


if __name__ == "__main__":
    # Process one at a time via CLI arg, or all sequentially
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    offset = 0

    for pdf_name, meta in SOURCES.items():
        if target != "all" and target not in pdf_name.lower():
            continue
        n = load_one(pdf_name, meta, offset)
        offset += n
        print()
