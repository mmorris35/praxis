import os
import chromadb
import yaml
from pathlib import Path

_client = None
_collection = None
_config = None

def _load_config():
    global _config
    if _config is None:
        cfg_path = Path(__file__).parent.parent / "config" / "gateway.yaml"
        with open(cfg_path) as f:
            _config = yaml.safe_load(f)
    return _config

def _get_collection():
    global _client, _collection
    if _collection is None:
        cfg = _load_config()["rag"]
        chroma_path = str(Path(__file__).parent.parent / cfg["chroma_path"])
        _client = chromadb.PersistentClient(path=chroma_path)
        _collection = _client.get_collection(cfg["collection"])
    return _collection


def _expand_queries(question: str) -> list[str]:
    """Use LLM to generate alternative search queries for better retrieval."""
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if not (anthropic_key or openai_key):
        return [question]

    prompt = f"""Generate 3 alternative search queries for finding the answer to this mortgage underwriting question in agency guidelines (FHA, Freddie Mac, USDA). Each query should use different terminology or focus on a different aspect.

Question: {question}

Return ONLY 3 queries, one per line, no numbering or bullets."""

    try:
        if anthropic_key:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            resp = client.messages.create(
                model="claude-haiku-4-20250414",
                max_tokens=200,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}],
            )
            lines = [l.strip() for l in resp.content[0].text.strip().split("\n") if l.strip()]
        elif openai_key:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=200,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}],
            )
            lines = [l.strip() for l in resp.choices[0].message.content.strip().split("\n") if l.strip()]
        else:
            return [question]

        return [question] + lines[:3]
    except Exception:
        return [question]


def retrieve(query: str, top_k: int = None, expand: bool = True) -> list[dict]:
    """Retrieve chunks using multi-query expansion for better recall."""
    cfg = _load_config()["rag"]
    if top_k is None:
        top_k = cfg["top_k"]
    col = _get_collection()

    # Generate expanded queries
    if expand:
        queries = _expand_queries(query)
    else:
        queries = [query]

    # Retrieve from each query, merge by score
    seen_ids = {}  # id -> (chunk_dict, distance)

    per_query_k = max(top_k, 8)  # get enough from each query
    for q in queries:
        results = col.query(query_texts=[q], n_results=per_query_k)
        for i in range(len(results["ids"][0])):
            chunk_id = results["ids"][0][i]
            distance = results["distances"][0][i] if results.get("distances") else 999
            meta = results["metadatas"][0][i]

            if chunk_id not in seen_ids or distance < seen_ids[chunk_id][1]:
                seen_ids[chunk_id] = ({
                    "id": chunk_id,
                    "text": results["documents"][0][i],
                    "source": meta.get("source", ""),
                    "agency": meta.get("short", meta.get("agency", "")),
                    "section": meta.get("section", ""),
                    "start_page": meta.get("start_page", ""),
                    "end_page": meta.get("end_page", ""),
                    "distance": distance,
                }, distance)

    # Sort by best distance, take top_k
    all_chunks = [v[0] for v in sorted(seen_ids.values(), key=lambda x: x[1])]
    return all_chunks[:top_k]


def format_context(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[Source {i}] {c['agency']} — {c['source']}, Section: {c['section']}, Pages {c['start_page']}–{c['end_page']}\n{c['text']}")
    return "\n\n---\n\n".join(parts)


def extract_sources(chunks: list[dict]) -> list[dict]:
    seen = set()
    sources = []
    for c in chunks:
        key = (c["source"], c["section"], str(c["start_page"]))
        if key not in seen:
            seen.add(key)
            sources.append({"source": c["source"], "section": c["section"], "page": c["start_page"]})
    return sources
