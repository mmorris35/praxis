#!/usr/bin/env python3
"""Full ingest with mappings and all frameworks."""
import json
import re
import chromadb
from pathlib import Path
from core.gateway.rag import LocalEmbeddingFunction

DATA_DIR = Path(__file__).parent.parent.parent / "examples" / "cmmc-buddy" / "data"
STRUCTURED_DIR = DATA_DIR / "structured"
CHROMA_DIR = Path(__file__).parent.parent.parent / "examples" / "cmmc-buddy" / "data" / "chroma"

# Load 800-171 to 800-53 mappings
MAPPING_FILE = STRUCTURED_DIR / "800-171-to-800-53-mapping.json"
if MAPPING_FILE.exists():
    with open(MAPPING_FILE) as f:
        MAPPINGS_171_TO_53 = json.load(f)
else:
    MAPPINGS_171_TO_53 = {}

SOURCES = {
    "800-53-rev5.json": {"name": "NIST SP 800-53 Rev 5", "short": "800-53"},
    "800-171-rev3.json": {"name": "NIST SP 800-171 Rev 3", "short": "800-171"},
    "csf-2.0.json": {"name": "NIST CSF 2.0", "short": "CSF-2.0"},
    "fedramp-high.json": {"name": "FedRAMP HIGH Baseline", "short": "FedRAMP-HIGH"},
}


def normalize_id(oscal_id):
    match = re.search(r'(\d+)\.(\d+)\.(\d+)', oscal_id)
    if match:
        return '.'.join(str(int(p)) for p in match.groups())
    return None

def extract_prose(parts):
    if not parts: return ""
    texts = []
    for part in parts:
        if part.get("prose"): texts.append(part["prose"])
        if part.get("parts"): texts.append(extract_prose(part["parts"]))
    return "\n".join(texts)

def extract_controls(data, source_info):
    chunks = []
    catalog = data.get("catalog", {})
    
    def process_control(control, family_id="", family_title=""):
        ctrl_id = control.get("id", "").upper()
        title = control.get("title", "")
        trad_id = normalize_id(ctrl_id) or ctrl_id
        
        parts = [f"Control {trad_id}: {title}"]
        if family_title:
            parts.append(f"Family: {family_title}")
        
        # Add mapping info for 800-171
        if source_info["short"] == "800-171" and trad_id in MAPPINGS_171_TO_53:
            mapped = MAPPINGS_171_TO_53[trad_id]
            parts.append(f"Maps to 800-53: {', '.join(mapped)}")
        
        prose = extract_prose(control.get("parts", []))
        if prose:
            parts.append(prose)
        
        text = "\n\n".join(parts)
        if text.strip():
            chunks.append({
                "id": f"{source_info['short']}_{ctrl_id}",
                "text": text,
                "source": source_info["short"],
                "control_id": trad_id,
                "control_title": title,
                "family": family_id,
                "family_title": family_title,
            })
        
        for enh in control.get("controls", []):
            process_control(enh, family_id, family_title)
    
    for group in catalog.get("groups", []):
        for control in group.get("controls", []):
            process_control(control, group.get("id", "").upper(), group.get("title", ""))
    
    return chunks

def main():
    all_chunks = []
    for filename, source_info in SOURCES.items():
        filepath = STRUCTURED_DIR / filename
        if not filepath.exists():
            print(f"Skipping: {filename} (not found)")
            continue
        print(f"Processing: {source_info['name']}")
        with open(filepath) as f:
            data = json.load(f)
        chunks = extract_controls(data, source_info)
        print(f"  {len(chunks)} controls")
        all_chunks.extend(chunks)
    
    print(f"\nTotal: {len(all_chunks)} controls")
    
    # Create collection with local SentenceTransformer (all-MiniLM-L6-v2) — matches the gateway query side
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try: client.delete_collection("cmmc-guidelines")
    except: pass

    ef = LocalEmbeddingFunction()
    collection = client.create_collection(name="cmmc-guidelines", embedding_function=ef)

    print("Indexing with all-MiniLM-L6-v2 (local)...")
    batch_size = 50
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i+batch_size]
        collection.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[{
                "source": c["source"],
                "section": c["control_id"],
                "control_id": c["control_id"],
                "control_title": c["control_title"],
                "family": c["family"],
            } for c in batch],
        )
        print(f"  Batch {i//batch_size + 1}: {len(batch)} indexed")
    
    print(f"\nDone! {len(all_chunks)} controls indexed")

if __name__ == "__main__":
    main()
