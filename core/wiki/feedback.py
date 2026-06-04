"""Bidirectional RAG feedback — ingest wiki pages back into ChromaDB."""

import logging
import chromadb
from core.gateway.rag import OllamaEmbeddingFunction
from core.wiki.models import WikiConfig, WikiPage

logger = logging.getLogger("praxis.wiki")


class WikiFeedback:
    """Ingests generated wiki pages back into ChromaDB for retrieval."""

    WIKI_PREFIX = "wiki:"

    def __init__(self, config: WikiConfig, chroma_client: chromadb.ClientAPI | None = None) -> None:
        self.config = config
        self._client: chromadb.ClientAPI | None = chroma_client
        self._collection: chromadb.Collection | None = None

    def _get_collection(self) -> chromadb.Collection:
        if self._collection is None:
            if self._client is None:
                self._client = chromadb.PersistentClient(path=self.config.chroma_path)
            embedding_fn = OllamaEmbeddingFunction(
                model=self.config.embedding_model,
                base_url=self.config.ollama_url,
            )
            self._collection = self._client.get_or_create_collection(
                name=self.config.collection_name,
                embedding_function=embedding_fn,
            )
        return self._collection

    def ingest_pages(self, pages: list[WikiPage]) -> int:
        """Upsert wiki pages into ChromaDB. Returns count of ingested pages."""
        col = self._get_collection()
        ids = [f"{self.WIKI_PREFIX}{p.slug}" for p in pages]
        documents = [p.content for p in pages]
        metadatas = [
            {
                "source": "wiki",
                "layer": "wiki-generated",
                "control_id": p.slug,
                "control_title": p.title,
                "wiki_layers": ",".join(p.layers),
            }
            for p in pages
        ]

        col.upsert(ids=ids, documents=documents, metadatas=metadatas)
        logger.info(f"Ingested {len(pages)} wiki pages into ChromaDB")
        return len(pages)

    def remove_stale(self, current_slugs: list[str]) -> int:
        """Remove wiki chunks for pages that no longer exist."""
        col = self._get_collection()
        all_results = col.get(where={"source": "wiki"}, include=[])
        existing_ids = set(all_results["ids"])
        current_ids = {f"{self.WIKI_PREFIX}{s}" for s in current_slugs}
        stale_ids = list(existing_ids - current_ids)

        if stale_ids:
            col.delete(ids=stale_ids)
            logger.info(f"Removed {len(stale_ids)} stale wiki chunks")
        return len(stale_ids)
