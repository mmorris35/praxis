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
def knowledge_search(query: str, top_k: int = 10) -> dict:
    """Search the Praxis knowledge base for documentation, controls, and API syntax.

    Returns ranked context passages with source attribution. Use this instead of
    guessing at API parameters, compliance requirements, or domain-specific syntax.

    Args:
        query: Natural language search query (e.g. "MS Graph $filter syntax for users").
        top_k: Number of results to return (1-25, default 10).
    """
    from core.gateway.rag import retrieve, format_context, extract_sources

    top_k = max(1, min(top_k, 25))

    if len(query) > 2000:
        query = query[:2000]

    chunks = retrieve(query, top_k=top_k)

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
    return {
        "collection": cfg.get("collection", "praxis"),
        "chroma_path": cfg.get("chroma_path", "data/chroma"),
    }
