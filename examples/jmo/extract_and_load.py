#!/usr/bin/env python3
"""Extract text from guideline PDFs, chunk by section, load into ChromaDB."""

import os
import re
import pymupdf
import chromadb
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
PDF_DIR = DATA_DIR / "pdfs"
CHROMA_DIR = DATA_DIR / "chroma"

SOURCES = {
    "FHA_Handbook_4000.1.pdf": {
        "name": "FHA Handbook 4000.1",
        "agency": "HUD/FHA",
        "short": "FHA",
    },
    "Freddie_Mac_Seller_Servicer_Guide.pdf": {
        "name": "Freddie Mac Seller/Servicer Guide",
        "agency": "Freddie Mac",
        "short": "Freddie",
    },
    "USDA_HB-1-3555_Guaranteed_Loan.pdf": {
        "name": "USDA HB-1-3555 Guaranteed Loan Program",
        "agency": "USDA Rural Development",
        "short": "USDA",
    },
}

# Section header patterns — checked against ALL lines, not just the first
SECTION_PATTERNS = [
    # FHA multi-level: "II. ORIGINATION THROUGH POST-CLOSING/ENDORSEMENT"
    re.compile(r'^((?:I{1,3}|IV|V|VI)\.\s+[A-Z][A-Z /\-]+)'),
    # FHA sub-sections: "A. Title II Insured Housing Programs"
    re.compile(r'^([A-Z]\.\s+[A-Z][A-Za-z ]+(?:Programs?|Mortgages?|Properties|Requirements|Borrower|Lenders?))'),
    # FHA numbered: "5. Manual Underwriting of the Borrower"
    re.compile(r'^(\d+\.\s+[A-Z][A-Za-z ]{10,})'),
    # USDA: "CHAPTER 11: RATIO ANALYSIS"
    re.compile(r'^(CHAPTER\s+\d+[:\s]+[A-Z][A-Z /\-]+)', re.IGNORECASE),
    # USDA paragraphs: "Paragraph 11.2 The Ratios"
    re.compile(r'^(Paragraph\s+[\d.]+\s+.+)', re.IGNORECASE),
    # Freddie: "5201.1" style
    re.compile(r'^(\d{4}\.\d+(?:\.\d+)?)\s+[A-Z]'),
    # Freddie chapter: "Chapter 5201"
    re.compile(r'^(Chapter\s+\d{4})', re.IGNORECASE),
    # Generic section
    re.compile(r'^(Section\s+[\d.]+\s+.+)', re.IGNORECASE),
]

# Lines to skip when scanning for headers (TOC, footers, etc.)
SKIP_PATTERNS = [
    re.compile(r'^\d+$'),                          # bare page numbers
    re.compile(r'^Handbook\s+\d+'),                 # "Handbook 4000.1"
    re.compile(r'^Effective Date'),                  # date lines
    re.compile(r'^\*Refer'),                         # reference notes
    re.compile(r'^HB-\d'),                           # "HB-1-3555"
    re.compile(r'^Revised'),                         # revision notes
    re.compile(r'^\(\d{2}-\d{2}-\d{2}\)'),          # date codes
]


def extract_pages(pdf_path: Path) -> list[dict]:
    """Extract text from each page of a PDF."""
    doc = pymupdf.open(str(pdf_path))
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        if text.strip():
            pages.append({"page": i + 1, "text": text.strip()})
    doc.close()
    return pages


def find_section_header(text: str) -> str | None:
    """Scan all lines of the page text for the deepest (most specific) section header."""
    best_header = None
    for line in text.split("\n"):
        line = line.strip()
        if not line or len(line) < 3:
            continue
        # Skip noise
        if any(sp.match(line) for sp in SKIP_PATTERNS):
            continue
        for pattern in SECTION_PATTERNS:
            m = pattern.match(line)
            if m:
                candidate = m.group(1).strip()
                # Prefer the most specific (last found) header
                best_header = candidate
                break  # matched a pattern, move to next line
    return best_header


def build_section_trail(page_text: str, current_trail: list[str]) -> list[str]:
    """Build a hierarchical section trail from page content.
    Returns a list like ["II. ORIGINATION", "A. Title II Programs", "5. Manual Underwriting"]
    """
    trail = list(current_trail)  # copy

    for line in page_text.split("\n"):
        line = line.strip()
        if not line or len(line) < 3:
            continue
        if any(sp.match(line) for sp in SKIP_PATTERNS):
            continue

        # Check each pattern — they're ordered from broadest to most specific
        for level, pattern in enumerate(SECTION_PATTERNS):
            m = pattern.match(line)
            if m:
                header = m.group(1).strip()
                # Trim trail to this level and add
                trail = trail[:level] + [header]
                break

    return trail


def format_section(trail: list[str]) -> str:
    """Format a section trail into a readable string."""
    if not trail:
        return "General"
    # Use the most specific (last) element, but include parent for context
    if len(trail) == 1:
        return trail[0]
    # Show last 2-3 levels for context
    return " > ".join(trail[-3:])


def chunk_pages(pages: list[dict], source_meta: dict, target_tokens: int = 600) -> list[dict]:
    """Chunk pages into ~target_tokens sized pieces with hierarchical section tracking."""
    chunks = []
    current_text = ""
    current_start_page = 1
    section_trail = []

    for page in pages:
        # Update section trail from this page
        new_trail = build_section_trail(page["text"], section_trail)
        if new_trail:
            section_trail = new_trail

        combined_len = len(current_text) + len(page["text"])
        estimated_tokens = combined_len / 4

        if estimated_tokens > target_tokens and current_text:
            chunks.append({
                "text": current_text.strip(),
                "source": source_meta["name"],
                "agency": source_meta["agency"],
                "short": source_meta["short"],
                "section": format_section(section_trail),
                "start_page": current_start_page,
                "end_page": page["page"] - 1,
            })
            current_text = page["text"]
            current_start_page = page["page"]
        else:
            if current_text:
                current_text += "\n\n" + page["text"]
            else:
                current_text = page["text"]
                current_start_page = page["page"]

    if current_text.strip():
        chunks.append({
            "text": current_text.strip(),
            "source": source_meta["name"],
            "agency": source_meta["agency"],
            "short": source_meta["short"],
            "section": format_section(section_trail),
            "start_page": current_start_page,
            "end_page": pages[-1]["page"] if pages else current_start_page,
        })

    return chunks


def main():
    print("=" * 60)
    print("Mortgage Guidelines — Extract, Chunk & Load")
    print("=" * 60)

    all_chunks = []

    for pdf_name, meta in SOURCES.items():
        pdf_path = PDF_DIR / pdf_name
        if not pdf_path.exists():
            print(f"\n⚠ Skipping {pdf_name} (not found)")
            continue

        print(f"\n📄 Processing: {meta['name']}")
        pages = extract_pages(pdf_path)
        print(f"   Extracted {len(pages)} pages")

        chunks = chunk_pages(pages, meta)
        print(f"   Created {len(chunks)} chunks")

        # Stats
        total_chars = sum(len(c["text"]) for c in chunks)
        avg_tokens = (total_chars / len(chunks)) / 4 if chunks else 0
        print(f"   Avg chunk size: ~{avg_tokens:.0f} tokens")

        # Section distribution
        sections = {}
        for c in chunks:
            s = c["section"]
            sections[s] = sections.get(s, 0) + 1
        print(f"   Unique sections: {len(sections)}")
        # Show top 5
        for s, count in sorted(sections.items(), key=lambda x: -x[1])[:5]:
            print(f"     {s}: {count} chunks")

        all_chunks.extend(chunks)

    print(f"\n{'=' * 60}")
    print(f"Total chunks: {len(all_chunks)}")

    # Load into ChromaDB
    print(f"\n📦 Loading into ChromaDB at {CHROMA_DIR}")
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    try:
        client.delete_collection("guidelines")
    except Exception:
        pass

    collection = client.create_collection(
        name="guidelines",
        metadata={"description": "Mortgage underwriting guidelines"},
    )

    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        collection.add(
            ids=[f"chunk_{i + j}" for j in range(len(batch))],
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
        print(f"   Loaded {min(i + batch_size, len(all_chunks))}/{len(all_chunks)} chunks")

    print(f"\n✅ Done! Collection '{collection.name}' has {collection.count()} documents")

    # Test queries
    test_queries = [
        "minimum credit score FHA",
        "debt-to-income ratio limits",
        "gift funds for down payment",
    ]
    for q in test_queries:
        print(f"\n🔍 Test: '{q}'")
        results = collection.query(query_texts=[q], n_results=3)
        for j, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
            print(f"   [{j+1}] {meta['short']} | {meta['section']} | p.{meta['start_page']}–{meta['end_page']}")
            print(f"       {doc[:150].replace(chr(10), ' ')}...")


if __name__ == "__main__":
    main()
