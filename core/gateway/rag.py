import os
import re
import requests
import chromadb
import yaml
from pathlib import Path
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

_client = None
_collection = None
_config = None
_embedding_fn = None


class OllamaEmbeddingFunction(EmbeddingFunction):
    """Custom embedding function using nomic-embed-text via Ollama."""
    def __init__(self, model="nomic-embed-text", base_url="http://100.87.147.89:11434"):
        self._model = model
        self._base_url = base_url
    
    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            resp = requests.post(
                f"{self._base_url}/api/embeddings",
                json={"model": self._model, "prompt": text},
                timeout=30
            )
            if resp.status_code == 200:
                embeddings.append(resp.json()["embedding"])
            else:
                raise Exception(f"Embedding failed: {resp.text}")
        return embeddings
    
    def name(self) -> str:
        return "ollama-nomic-embed-text"


def _load_config():
    global _config
    if _config is None:
        cfg_path = Path(__file__).parent.parent / "config" / "gateway.yaml"
        with open(cfg_path) as f:
            _config = yaml.safe_load(f)
    return _config


def _get_embedding_fn():
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = OllamaEmbeddingFunction()
    return _embedding_fn


def _get_collection():
    global _client, _collection
    if _collection is None:
        cfg = _load_config()["rag"]
        chroma_path = str(Path(__file__).parent.parent / cfg["chroma_path"])
        _client = chromadb.PersistentClient(path=chroma_path)
        _collection = _client.get_collection(
            cfg["collection"],
            embedding_function=_get_embedding_fn()
        )
    return _collection


def _extract_control_refs(query):
    """Extract control references from query."""
    refs = []
    # NIST style: 3.1.1, 3.1.2, etc
    refs.extend(re.findall(r'\b(\d+\.\d+\.\d+)\b', query))
    # 800-53 style: AC-2, SI-3, etc
    refs.extend(re.findall(r'\b([A-Z]{2}-\d+(?:\.\d+)?)\b', query, re.IGNORECASE))
    # CMMC style: AC.L2-3.1.1-a
    refs.extend(re.findall(r'\b(AC\.L2-\d+\.\d+\.\d+-[a-z])\b', query, re.IGNORECASE))
    refs.extend(re.findall(r'\b([A-Z]{2}\.L2-\d+\.\d+\.\d+(?:-[a-z])?)\b', query, re.IGNORECASE))
    return list(set(refs))


def retrieve(query: str, top_k: int = None, expand: bool = False) -> list[dict]:
    """Hybrid retrieval: exact match + semantic search."""
    cfg = _load_config()["rag"]
    if top_k is None:
        top_k = cfg["top_k"]
    col = _get_collection()

    seen_ids = {}
    
    # 1. Exact control reference match
    control_refs = _extract_control_refs(query)
    for ref in control_refs:
        # Try CMMC format
        cmmc_id = f"CMMC_{ref.upper()}"
        try:
            exact = col.get(ids=[cmmc_id])
            if exact["documents"]:
                for i, doc in enumerate(exact["documents"]):
                    chunk_id = exact["ids"][i]
                    meta = exact["metadatas"][i]
                    seen_ids[chunk_id] = ({
                        "id": chunk_id,
                        "text": doc,
                        "source": meta.get("source", ""),
                        "agency": meta.get("source", ""),
                        "section": meta.get("control_id", ""),
                        "control_id": meta.get("control_id", ""),
                        "control_title": meta.get("control_title", ""),
                        "start_page": "",
                        "end_page": "",
                        "distance": 0,
                    }, 0)
        except:
            pass
        
        # Try NIST control_id
        try:
            exact = col.get(where={"control_id": ref})
            if exact["documents"]:
                for i, doc in enumerate(exact["documents"]):
                    chunk_id = exact["ids"][i]
                    meta = exact["metadatas"][i]
                    if chunk_id not in seen_ids:
                        seen_ids[chunk_id] = ({
                            "id": chunk_id,
                            "text": doc,
                            "source": meta.get("source", ""),
                            "agency": meta.get("source", ""),
                            "section": meta.get("control_id", ""),
                            "control_id": meta.get("control_id", ""),
                            "control_title": meta.get("control_title", ""),
                            "start_page": "",
                            "end_page": "",
                            "distance": 0.1,
                        }, 0.1)
        except:
            pass
    
    # 2. Semantic search
    results = col.query(query_texts=[query], n_results=top_k)
    for i in range(len(results["ids"][0])):
        chunk_id = results["ids"][0][i]
        distance = results["distances"][0][i] if results.get("distances") else 999
        meta = results["metadatas"][0][i]

        if chunk_id not in seen_ids or distance < seen_ids[chunk_id][1]:
            seen_ids[chunk_id] = ({
                "id": chunk_id,
                "text": results["documents"][0][i],
                "source": meta.get("source", ""),
                "agency": meta.get("source", ""),
                "section": meta.get("control_id", meta.get("section", "")),
                "control_id": meta.get("control_id", ""),
                "control_title": meta.get("control_title", ""),
                "start_page": "",
                "end_page": "",
                "distance": distance,
            }, distance)

    all_chunks = [v[0] for v in sorted(seen_ids.values(), key=lambda x: x[1])]
    return all_chunks[:top_k]


def format_context(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        ctrl_info = f"Control {c['control_id']}: {c['control_title']}" if c.get('control_title') else ""
        parts.append(f"[Source {i}] {c['source']} — {c['section']}\n{ctrl_info}\n{c['text']}")
    return "\n\n---\n\n".join(parts)


def extract_sources(chunks: list[dict]) -> list[dict]:
    seen = set()
    sources = []
    for c in chunks:
        key = (c.get("source", ""), c.get("control_id", c.get("section", "")))
        if key not in seen:
            seen.add(key)
            sources.append({
                "source": c.get("source", ""),
                "section": c.get("control_id", c.get("section", "")),
                "control_id": c.get("control_id", ""),
                "control_title": c.get("control_title", ""),
                "page": "",
            })
    return sources
