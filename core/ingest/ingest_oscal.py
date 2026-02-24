#!/usr/bin/env python3
"""Ingest NIST OSCAL JSON files into ChromaDB with proper chunking."""

import json
import chromadb
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
STRUCTURED_DIR = DATA_DIR / "structured"
CHROMA_DIR = DATA_DIR / "chroma"

SOURCES = {
    "800-53-rev5.json": {"name": "NIST SP 800-53 Rev 5", "short": "800-53"},
    "800-171-rev3.json": {"name": "NIST SP 800-171 Rev 3", "short": "800-171"},
    "csf-2.0.json": {"name": "NIST CSF 2.0", "short": "CSF-2.0"},
}


def extract_prose(parts):
    """Extract prose text from OSCAL parts structure."""
    if not parts:
        return ""
    texts = []
    for part in parts:
        if part.get("prose"):
            texts.append(part["prose"])
        if part.get("parts"):
            texts.append(extract_prose(part["parts"]))
    return "\n".join(texts)


def extract_controls(data, source_info):
    """Extract all controls from an OSCAL catalog."""
    chunks = []
    catalog = data.get("catalog", {})
    
    def process_control(control, family_id="", family_title=""):
        """Process a single control and its enhancements."""
        ctrl_id = control.get("id", "").upper()
        title = control.get("title", "")
        
        # Build the control text
        parts = []
        parts.append(f"Control {ctrl_id}: {title}")
        if family_title:
            parts.append(f"Family: {family_title}")
        
        # Get prose from parts
        prose = extract_prose(control.get("parts", []))
        if prose:
            parts.append(prose)
        
        # Get any props (like control baselines, etc)
        props = control.get("props", [])
        prop_texts = []
        for p in props:
            if p.get("name") and p.get("value"):
                prop_texts.append(f"{p['name']}: {p['value']}")
        if prop_texts:
            parts.append("Properties: " + ", ".join(prop_texts))
        
        # Get links/references
        links = control.get("links", [])
        link_texts = []
        for link in links:
            if link.get("rel") == "reference" and link.get("href"):
                link_texts.append(link["href"])
        if link_texts:
            parts.append("References: " + ", ".join(link_texts))
        
        text = "\n\n".join(parts)
        
        if text.strip():
            chunks.append({
                "id": f"{source_info['short']}_{ctrl_id}",
                "text": text,
                "source": source_info["short"],
                "source_name": source_info["name"],
                "control_id": ctrl_id,
                "control_title": title,
                "family": family_id,
                "family_title": family_title,
            })
        
        # Process control enhancements
        for enhancement in control.get("controls", []):
            process_control(enhancement, family_id, family_title)
    
    # Process groups (control families)
    for group in catalog.get("groups", []):
        family_id = group.get("id", "").upper()
        family_title = group.get("title", "")
        
        # Process controls in this family
        for control in group.get("controls", []):
            process_control(control, family_id, family_title)
        
        # Some catalogs have nested groups
        for subgroup in group.get("groups", []):
            sub_family_id = subgroup.get("id", "").upper()
            sub_family_title = subgroup.get("title", "")
            for control in subgroup.get("controls", []):
                process_control(control, sub_family_id, sub_family_title)
    
    return chunks


def load_into_chroma(chunks, collection_name="cmmc-guidelines"):
    """Load chunks into ChromaDB."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    # Delete existing collection
    try:
        client.delete_collection(collection_name)
        print(f"Deleted existing collection: {collection_name}")
    except:
        pass
    
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "CMMC/NIST compliance guidelines from OSCAL"}
    )
    
    ids = []
    documents = []
    metadatas = []
    
    for chunk in chunks:
        ids.append(chunk["id"])
        documents.append(chunk["text"])
        metadatas.append({
            "source": chunk["source"],
            "source_name": chunk["source_name"],
            "section": chunk["control_id"],
            "control_id": chunk["control_id"],
            "control_title": chunk["control_title"],
            "family": chunk["family"],
            "family_title": chunk["family_title"],
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
    
    for filename, source_info in SOURCES.items():
        filepath = STRUCTURED_DIR / filename
        if not filepath.exists():
            print(f"Warning: {filename} not found, skipping")
            continue
        
        print(f"\nProcessing: {source_info['name']}")
        with open(filepath) as f:
            data = json.load(f)
        
        chunks = extract_controls(data, source_info)
        print(f"  Extracted {len(chunks)} controls")
        
        # Show sample
        if chunks:
            sample = chunks[0]
            print(f"  Sample: {sample['control_id']} - {sample['control_title'][:50]}")
        
        all_chunks.extend(chunks)
    
    if all_chunks:
        print(f"\n{'='*50}")
        print(f"Loading {len(all_chunks)} total controls into ChromaDB...")
        load_into_chroma(all_chunks)
        print("Done!")
    else:
        print("No chunks to load!")


if __name__ == "__main__":
    main()


def normalize_control_id(oscal_id):
    """Convert OSCAL ID to traditional format for searchability.
    SP_800_171_03.01.01 -> 3.1.1
    """
    import re
    # Match patterns like 03.01.01
    match = re.search(r'(\d+)\.(\d+)\.(\d+)', oscal_id)
    if match:
        parts = [str(int(p)) for p in match.groups()]  # Remove leading zeros
        return '.'.join(parts)
    return None
