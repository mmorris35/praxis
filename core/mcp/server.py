"""MCP server exposing Praxis RAG as tools for coding agents."""

from fastmcp import FastMCP

mcp = FastMCP(
    "Praxis",
    instructions=(
        "Praxis is an expert-system knowledge base. Use knowledge_search "
        "to find authoritative documentation, compliance controls, and "
        "API syntax grounded in indexed sources — not guesses."
    ),
)


@mcp.tool
def knowledge_search(query: str, top_k: int = None) -> dict:
    """Search the Praxis knowledge base for documentation, controls, and API syntax.

    Returns ranked context passages with source attribution. Use this instead of
    guessing at API parameters, compliance requirements, or domain-specific syntax.

    Args:
        query: Natural language search query (e.g. "MS Graph $filter syntax for users").
        top_k: Number of results to return (1-25, default from gateway.yaml).
    """
    from core.gateway.rag import retrieve, format_context, extract_sources, _load_config

    if top_k is None:
        top_k = _load_config()["rag"].get("top_k", 10)
    top_k = max(1, min(top_k, 25))

    if len(query) > 2000:
        query = query[:2000]

    try:
        chunks = retrieve(query, top_k=top_k)
    except Exception as e:
        return {
            "context": f"Knowledge search failed: {type(e).__name__}",
            "sources": [],
            "error": True,
        }

    if not chunks:
        return {
            "context": "No relevant results found for this query.",
            "sources": [],
        }

    return {
        "context": format_context(chunks),
        "sources": extract_sources(chunks),
    }


@mcp.tool
def list_domains() -> dict:
    """List the knowledge domains available in this Praxis instance.

    Returns the configured ChromaDB collection(s) so the agent knows what
    corpora are available for querying.
    """
    from core.gateway.rag import _load_config

    cfg = _load_config()["rag"]
    collections = [cfg.get("collection", "praxis")]
    collections.extend(cfg.get("extra_collections", []))
    return {
        "collections": collections,
        "primary": cfg.get("collection", "praxis"),
        "chroma_path": cfg.get("chroma_path", "data/chroma"),
    }


@mcp.tool
def ingest_documents(
    collection: str,
    source_path: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    source_label: str = None,
) -> dict:
    """Ingest documents from a local directory or file into a Praxis collection.

    Reads .md, .txt, .json, .yaml, .html, .ps1, .py files from source_path,
    chunks them, embeds with the same bi-encoder used for queries, and stores
    in ChromaDB. Creates the collection if it doesn't exist. Automatically
    registers new collections in gateway.yaml.

    Args:
        collection: ChromaDB collection name (e.g. "sallyport-nist").
        source_path: Absolute path to a file or directory on this machine.
        chunk_size: Target chunk size in words (default 500).
        chunk_overlap: Overlap between chunks in words (default 50).
        source_label: Human label for the source (default: directory/file name).
    """
    import os
    import re
    from pathlib import Path
    import chromadb
    import yaml
    import hashlib

    from core.gateway.rag import LocalEmbeddingFunction, _load_config

    ALLOWED_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".html", ".htm",
                          ".ps1", ".py", ".sh", ".csv", ".xml", ".rst", ".adoc"}

    src = Path(source_path)
    if not src.exists():
        return {"error": True, "message": f"Path not found: {source_path}"}

    if not collection or not re.match(r"^[a-zA-Z0-9_-]+$", collection):
        return {"error": True, "message": "Collection name must be alphanumeric with hyphens/underscores only."}

    if source_label is None:
        source_label = src.name

    # Gather files
    files = []
    if src.is_file():
        if src.suffix.lower() in ALLOWED_EXTENSIONS:
            files.append(src)
        else:
            return {"error": True, "message": f"Unsupported file type: {src.suffix}"}
    else:
        for root, _, filenames in os.walk(src):
            for fn in filenames:
                fp = Path(root) / fn
                if fp.suffix.lower() in ALLOWED_EXTENSIONS:
                    files.append(fp)

    if not files:
        return {"error": True, "message": f"No ingestible files found at {source_path}"}

    # Read and chunk
    def chunk_text(text, size, overlap):
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + size
            chunk = " ".join(words[start:end])
            if chunk.strip():
                chunks.append(chunk)
            start += size - overlap
        return chunks

    all_chunks = []
    file_count = 0
    for fp in sorted(files):
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if not text.strip():
            continue
        file_count += 1
        rel_path = str(fp.relative_to(src)) if src.is_dir() else fp.name
        chunks = chunk_text(text, chunk_size, chunk_overlap)
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.sha256(f"{collection}:{rel_path}:{i}".encode()).hexdigest()[:16]
            all_chunks.append({
                "id": f"{collection}_{chunk_id}",
                "text": chunk,
                "source": source_label,
                "file": rel_path,
                "chunk_index": i,
            })

    if not all_chunks:
        return {"error": True, "message": "All files were empty or unreadable."}

    # Ingest into ChromaDB
    cfg = _load_config()["rag"]
    chroma_path = str(Path(__file__).parent.parent / cfg["chroma_path"])
    client = chromadb.PersistentClient(path=chroma_path)
    ef = LocalEmbeddingFunction()

    col = client.get_or_create_collection(name=collection, embedding_function=ef)

    batch_size = 50
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        col.upsert(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[{
                "source": c["source"],
                "file": c["file"],
                "chunk_index": c["chunk_index"],
            } for c in batch],
        )

    # Auto-register collection in gateway.yaml if new
    all_collections = [cfg.get("collection", "")]
    all_collections.extend(cfg.get("extra_collections", []))
    if collection not in all_collections:
        cfg_path = Path(__file__).parent.parent / "config" / "gateway.yaml"
        with open(cfg_path) as f:
            raw_cfg = yaml.safe_load(f)
        if "extra_collections" not in raw_cfg["rag"]:
            raw_cfg["rag"]["extra_collections"] = []
        raw_cfg["rag"]["extra_collections"].append(collection)
        with open(cfg_path, "w") as f:
            yaml.dump(raw_cfg, f, default_flow_style=False, sort_keys=False)
        # Clear cached config so next query picks up the new collection
        import core.gateway.rag as rag_mod
        rag_mod._config = None
        rag_mod._collections = {}
        registered = True
    else:
        registered = False

    return {
        "collection": collection,
        "files_processed": file_count,
        "chunks_created": len(all_chunks),
        "registered": registered,
        "message": f"Ingested {len(all_chunks)} chunks from {file_count} files into '{collection}'.",
    }


@mcp.tool
def delete_collection(collection: str) -> dict:
    """Delete a ChromaDB collection and unregister it from gateway.yaml.

    Use with caution — this permanently removes all documents in the collection.

    Args:
        collection: Name of the collection to delete.
    """
    import chromadb
    import yaml
    from pathlib import Path
    from core.gateway.rag import _load_config

    cfg = _load_config()["rag"]

    if collection == cfg.get("collection", ""):
        return {"error": True, "message": f"Cannot delete the primary collection '{collection}'."}

    chroma_path = str(Path(__file__).parent.parent / cfg["chroma_path"])
    client = chromadb.PersistentClient(path=chroma_path)

    try:
        client.delete_collection(collection)
    except Exception as e:
        return {"error": True, "message": f"Failed to delete collection: {e}"}

    # Remove from gateway.yaml
    cfg_path = Path(__file__).parent.parent / "config" / "gateway.yaml"
    with open(cfg_path) as f:
        raw_cfg = yaml.safe_load(f)
    extras = raw_cfg["rag"].get("extra_collections", [])
    if collection in extras:
        extras.remove(collection)
        with open(cfg_path, "w") as f:
            yaml.dump(raw_cfg, f, default_flow_style=False, sort_keys=False)

    # Clear cached config
    import core.gateway.rag as rag_mod
    rag_mod._config = None
    rag_mod._collections = {}

    return {"deleted": collection, "message": f"Collection '{collection}' deleted and unregistered."}
