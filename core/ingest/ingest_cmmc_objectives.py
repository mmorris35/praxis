#!/usr/bin/env python3
"""Ingest CMMC objectives with Graph API mapping."""
import json
import requests
import chromadb
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
STRUCTURED_DIR = DATA_DIR / "structured"
CHROMA_DIR = DATA_DIR / "chroma"

class OllamaEmbedding:
    def __init__(self, model="nomic-embed-text", base_url="http://100.87.147.89:11434"):
        self.model = model
        self.base_url = base_url
    def __call__(self, input):
        embeddings = []
        for text in input:
            resp = requests.post(f"{self.base_url}/api/embeddings", 
                json={"model": self.model, "prompt": text}, timeout=30)
            embeddings.append(resp.json()["embedding"])
        return embeddings
    def name(self): return "nomic-embed-text"

def main():
    # Load objectives
    with open(STRUCTURED_DIR / "cmmc-objectives-graph.json") as f:
        objectives = json.load(f)
    
    print(f"Processing {len(objectives)} CMMC objectives...")
    
    chunks = []
    for obj in objectives:
        ctrl_obj = obj["Control_Objective"]
        obj_text = obj["Objective_Text"]
        guidance = obj.get("assessor_guidance", {})
        
        # Build rich text for this objective
        parts = [
            f"CMMC Objective {ctrl_obj}: {obj_text}",
            "",
            f"What Assessor Wants: {guidance.get('what_assessor_wants', 'N/A')}",
            "",
            f"Evidence Type: {guidance.get('evidence_type', 'N/A')}",
            f"Automation Possible: {guidance.get('automation_possible', False)} ({guidance.get('automation_percentage', 0)}%)",
        ]
        
        # Add API endpoints
        auto = guidance.get("evidence_sources", {}).get("automated", {})
        api_endpoints = auto.get("api_endpoints", [])
        if api_endpoints:
            parts.append("")
            parts.append("Graph API Calls for Assessment:")
            for api in api_endpoints:
                endpoint = api.get("endpoint", "")
                method = api.get("method", "GET")
                purpose = api.get("purpose", "")
                parts.append(f"  • {method} {endpoint}")
                if purpose:
                    parts.append(f"    Purpose: {purpose}")
        
        # Add manual documents
        manual = guidance.get("evidence_sources", {}).get("manual", {})
        required_docs = manual.get("required_documents", [])
        if required_docs:
            parts.append("")
            parts.append("Required Manual Documentation:")
            for doc in required_docs:
                if isinstance(doc, dict):
                    doc_name = doc.get("document", doc.get("document_title", doc.get("name", "Document")))
                    contents = doc.get("contents", doc.get("purpose", doc.get("description", "")))
                    parts.append(f"  • {doc_name}")
                    if contents:
                        parts.append(f"    {contents[:100]}...")
                else:
                    parts.append(f"  • {doc}")
        
        # Add common gaps
        gaps = guidance.get("common_gaps", "")
        if gaps:
            parts.append("")
            parts.append(f"Common Gaps: {gaps}")
        
        # Add tips
        tips = guidance.get("assessor_tips", "")
        if tips:
            parts.append("")
            parts.append(f"Assessor Tips: {tips}")
        
        text = "\n".join(parts)
        
        # Extract control family (e.g., AC.L2-3.1.1-a -> AC, 3.1.1)
        family = ctrl_obj.split(".")[0] if "." in ctrl_obj else ""
        control_num = ""
        if "-" in ctrl_obj:
            # AC.L2-3.1.1-a -> 3.1.1
            parts_split = ctrl_obj.split("-")
            if len(parts_split) >= 2:
                control_num = parts_split[1]
        
        chunks.append({
            "id": f"CMMC_{ctrl_obj}",
            "text": text,
            "source": "CMMC-L2",
            "control_id": ctrl_obj,
            "control_title": obj_text,
            "family": family,
            "control_num": control_num,
        })
    
    # Add to existing collection
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = OllamaEmbedding()
    
    collection = client.get_collection("cmmc-guidelines", embedding_function=ef)
    
    print(f"Adding {len(chunks)} CMMC objective chunks...")
    batch_size = 25
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
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
    
    print(f"\nDone! Total chunks in collection: {collection.count()}")

if __name__ == "__main__":
    main()
