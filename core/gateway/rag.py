import os
import re
import requests
import chromadb
import yaml
from pathlib import Path
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

_client = None
_collections = {}
_config = None
_embedding_fn = None
_reranker = None


class LocalEmbeddingFunction(EmbeddingFunction):
    """Embedding function using sentence-transformers (no external server needed)."""
    def __init__(self, model="all-MiniLM-L6-v2"):
        self._model_name = model
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)

    def __call__(self, input: Documents) -> Embeddings:
        self._load()
        return self._model.encode(list(input)).tolist()

    def name(self) -> str:
        return f"st-{self._model_name}"


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
        _embedding_fn = LocalEmbeddingFunction()
    return _embedding_fn


def _get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker


def _rerank(query: str, chunks: list[dict], top_k: int) -> list[dict]:
    """Rerank chunks using cross-encoder for better relevance ordering."""
    if not chunks:
        return chunks
    reranker = _get_reranker()
    pairs = [(query, c["text"]) for c in chunks]
    scores = reranker.predict(pairs)
    scored = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]


def _get_client():
    global _client
    if _client is None:
        cfg = _load_config()["rag"]
        chroma_path = str(Path(__file__).parent.parent / cfg["chroma_path"])
        _client = chromadb.PersistentClient(path=chroma_path)
    return _client


def _get_collection(name=None):
    """Get a ChromaDB collection by name. Defaults to primary collection from config."""
    global _collections
    if name is None:
        cfg = _load_config()["rag"]
        name = cfg["collection"]
    if name not in _collections:
        client = _get_client()
        _collections[name] = client.get_collection(
            name, embedding_function=_get_embedding_fn()
        )
    return _collections[name]


def _get_all_collection_names():
    """Return list of all collection names to search."""
    cfg = _load_config()["rag"]
    names = [cfg["collection"]]
    extra = cfg.get("extra_collections", [])
    names.extend(extra)
    return names


def _extract_control_refs(query):
    """Extract control references from query."""
    refs = []
    refs.extend(re.findall(r'\b(\d+\.\d+\.\d+)\b', query))
    refs.extend(re.findall(r'\b([A-Z]{2}-\d+(?:\.\d+)?)\b', query, re.IGNORECASE))
    refs.extend(re.findall(r'\b(AC\.L2-\d+\.\d+\.\d+-[a-z])\b', query, re.IGNORECASE))
    refs.extend(re.findall(r'\b([A-Z]{2}\.L2-\d+\.\d+\.\d+(?:-[a-z])?)\b', query, re.IGNORECASE))
    return list(set(refs))


def retrieve(query: str, top_k: int = None, expand: bool = False) -> list[dict]:
    """Hybrid retrieval across all configured collections."""
    cfg = _load_config()["rag"]
    if top_k is None:
        top_k = cfg["top_k"]

    seen_ids = {}
    collection_names = _get_all_collection_names()

    for col_name in collection_names:
        try:
            col = _get_collection(col_name)
        except Exception:
            continue

        # Exact control reference match (only for cmmc/nist collections)
        if "cmmc" in col_name or "nist" in col_name or col_name == cfg["collection"]:
            control_refs = _extract_control_refs(query)
            for ref in control_refs:
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

        # Semantic search
        ann_k = max(top_k, 20)
        results = col.query(query_texts=[query], n_results=ann_k)
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
                    "section": meta.get("control_id", meta.get("section", meta.get("category", ""))),
                    "control_id": meta.get("control_id", meta.get("title", "")),
                    "control_title": meta.get("control_title", meta.get("title", "")),
                    "start_page": "",
                    "end_page": "",
                    "distance": distance,
                }, distance)

    all_chunks = [v[0] for v in sorted(seen_ids.values(), key=lambda x: x[1])]
    return _rerank(query, all_chunks, top_k)


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
