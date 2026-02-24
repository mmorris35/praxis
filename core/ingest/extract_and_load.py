#!/usr/bin/env python3
"""Extract text from CMMC/NIST PDFs, chunk by section, load into ChromaDB."""

import os
import re
import pymupdf
import chromadb
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
PDF_DIR = DATA_DIR / "pdfs"
CHROMA_DIR = DATA_DIR / "chroma"

SOURCES = {
    "NIST-SP-800-171r2.pdf": {
        "name": "NIST SP 800-171 Rev 2",
        "agency": "NIST",
        "short": "800-171r2",
        "description": "Protecting CUI in Nonfederal Systems (Rev 2)"
    },
    "NIST-SP-800-171r3.pdf": {
        "name": "NIST SP 800-171 Rev 3",
        "agency": "NIST",
        "short": "800-171r3",
        "description": "Protecting CUI in Nonfederal Systems (Rev 3 - Latest)"
    },
    "NIST-SP-800-171A.pdf": {
        "name": "NIST SP 800-171A",
        "agency": "NIST", 
        "short": "800-171A",
        "description": "Assessing Security Requirements for CUI"
    },
    "NIST-SP-800-171Ar3.pdf": {
        "name": "NIST SP 800-171A Rev 3",
        "agency": "NIST", 
        "short": "800-171Ar3",
        "description": "Assessing Security Requirements for CUI (Rev 3)"
    },
    "NIST-SP-800-172.pdf": {
        "name": "NIST SP 800-172",
        "agency": "NIST",
        "short": "800-172",
        "description": "Enhanced Security Requirements for CUI"
    },
    "NIST-SP-800-53r5.pdf": {
        "name": "NIST SP 800-53 Rev 5",
        "agency": "NIST",
        "short": "800-53",
        "description": "Security and Privacy Controls for Information Systems"
    },
    "NIST-SP-800-37r2.pdf": {
        "name": "NIST SP 800-37 Rev 2",
        "agency": "NIST",
        "short": "800-37",
        "description": "Risk Management Framework for Information Systems"
    },
    "NIST-CSF-2.0.pdf": {
        "name": "NIST Cybersecurity Framework 2.0",
        "agency": "NIST",
        "short": "CSF-2.0",
        "description": "Cybersecurity Framework 2.0"
    },
}

# Section header patterns for NIST documents
SECTION_PATTERNS = [
    # NIST control families: "3.1 ACCESS CONTROL"
    re.compile(r'^(3\.\d+\s+[A-Z][A-Z\s]+)$'),
    # Individual controls: "3.1.1" or "3.1.22"
    re.compile(r'^(3\.\d+\.\d+)\s'),
    # NIST 800-53 controls: "AC-1", "SI-7"
    re.compile(r'^([A-Z]{2}-\d+(?:\(\d+\))?)\s'),
    # Chapter/Section headers
    re.compile(r'^(CHAPTER\s+\d+)', re.IGNORECASE),
    re.compile(r'^(APPENDIX\s+[A-Z])', re.IGNORECASE),
    # Section numbers: "2.1", "3.4.2"
    re.compile(r'^(\d+\.\d+(?:\.\d+)?)\s+[A-Z]'),
    # Generic section
    re.compile(r'^(Section\s+[\d.]+)', re.IGNORECASE),
]

# Lines to skip
SKIP_PATTERNS = [
    re.compile(r'^\d+$'),                          # bare page numbers
    re.compile(r'^NIST\s+SP\s+800'),               # header lines
    re.compile(r'^This publication'),              # boilerplate
    re.compile(r'^\s*$'),                          # empty lines
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
        if not line or len(line) > 120:
            continue
        skip = False
        for sp in SKIP_PATTERNS:
            if sp.match(line):
                skip = True
                break
        if skip:
            continue
        for pattern in SECTION_PATTERNS:
            m = pattern.match(line)
            if m:
                best_header = m.group(1).strip()
    return best_header


def chunk_document(pdf_path: Path, source_info: dict) -> list[dict]:
    """Extract and chunk a PDF document."""
    pages = extract_pages(pdf_path)
    chunks = []
    current_section = "Introduction"
    current_text = []
    
    for page_data in pages:
        page_num = page_data["page"]
        text = page_data["text"]
        
        # Check for new section
        new_section = find_section_header(text)
        if new_section and new_section != current_section:
            # Save previous chunk if substantial
            if current_text and len(" ".join(current_text)) > 200:
                chunks.append({
                    "text": " ".join(current_text),
                    "section": current_section,
                    "source": source_info["short"],
                    "source_name": source_info["name"],
                    "agency": source_info["agency"],
                })
            current_section = new_section
            current_text = []
        
        current_text.append(text)
        
        # Chunk if getting long (roughly 1500 words)
        if len(" ".join(current_text)) > 8000:
            chunks.append({
                "text": " ".join(current_text),
                "section": current_section,
                "source": source_info["short"],
                "source_name": source_info["name"],
                "agency": source_info["agency"],
            })
            current_text = []
    
    # Final chunk
    if current_text and len(" ".join(current_text)) > 200:
        chunks.append({
            "text": " ".join(current_text),
            "section": current_section,
            "source": source_info["short"],
            "source_name": source_info["name"],
            "agency": source_info["agency"],
        })
    
    return chunks


def load_into_chroma(chunks: list[dict], collection_name: str = "cmmc-guidelines"):
    """Load chunks into ChromaDB."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    # Delete existing collection if present
    try:
        client.delete_collection(collection_name)
        print(f"Deleted existing collection: {collection_name}")
    except:
        pass
    
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "CMMC/NIST compliance guidelines"}
    )
    
    ids = []
    documents = []
    metadatas = []
    
    for i, chunk in enumerate(chunks):
        chunk_id = f"{chunk['source']}_{i:04d}"
        ids.append(chunk_id)
        documents.append(chunk["text"])
        metadatas.append({
            "section": chunk["section"],
            "source": chunk["source"],
            "source_name": chunk["source_name"],
            "agency": chunk["agency"],
        })
    
    # Add in batches
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        collection.add(
            ids=ids[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end],
        )
        print(f"Added batch {i//batch_size + 1}: {end - i} chunks")
    
    print(f"\nTotal chunks loaded: {len(ids)}")
    return collection


def main():
    all_chunks = []
    
    for pdf_name, source_info in SOURCES.items():
        pdf_path = PDF_DIR / pdf_name
        if not pdf_path.exists():
            print(f"Warning: {pdf_name} not found, skipping")
            continue
        
        print(f"\nProcessing: {source_info['name']}")
        chunks = chunk_document(pdf_path, source_info)
        print(f"  Extracted {len(chunks)} chunks")
        all_chunks.extend(chunks)
    
    if all_chunks:
        print(f"\n{'='*50}")
        print(f"Loading {len(all_chunks)} total chunks into ChromaDB...")
        load_into_chroma(all_chunks)
        print("Done!")
    else:
        print("No chunks to load!")


if __name__ == "__main__":
    main()
