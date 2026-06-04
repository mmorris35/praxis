"""Wiki page generator — distills ChromaDB chunks into structured markdown pages."""

import logging
import time
import chromadb
import anthropic
from collections import defaultdict
from datetime import datetime, timezone
from slugify import slugify
from core.gateway.rag import OllamaEmbeddingFunction
from core.wiki.models import WikiConfig, WikiPage, ConceptCluster

logger = logging.getLogger("praxis.wiki")


class WikiGenerator:
    """Generates wiki pages from ChromaDB knowledge chunks using LLM distillation."""

    def __init__(self, config: WikiConfig, chroma_client: chromadb.ClientAPI | None = None) -> None:
        self.config = config
        self._client: chromadb.ClientAPI | None = chroma_client
        self._collection: chromadb.Collection | None = None
        self._anthropic: anthropic.Anthropic | None = None

    def _get_anthropic(self) -> anthropic.Anthropic:
        if self._anthropic is None:
            self._anthropic = anthropic.Anthropic()
        return self._anthropic

    def _get_collection(self) -> chromadb.Collection:
        if self._collection is None:
            if self._client is None:
                self._client = chromadb.PersistentClient(path=self.config.chroma_path)
            embedding_fn = OllamaEmbeddingFunction(
                model=self.config.embedding_model,
                base_url=self.config.ollama_url,
            )
            self._collection = self._client.get_collection(
                name=self.config.collection_name,
                embedding_function=embedding_fn,
            )
        return self._collection

    def extract_chunks(self) -> list[dict]:
        """Pull all chunks from the ChromaDB collection with metadata."""
        col = self._get_collection()
        count = col.count()
        if count == 0:
            return []

        batch_size = 1000
        all_chunks = []
        for offset in range(0, count, batch_size):
            results = col.get(
                limit=batch_size,
                offset=offset,
                include=["documents", "metadatas"],
            )
            for i, doc_id in enumerate(results["ids"]):
                meta = (results["metadatas"][i] or {}) if results["metadatas"] else {}
                all_chunks.append({
                    "id": doc_id,
                    "text": results["documents"][i],
                    "source": meta.get("source", "unknown"),
                    "control_id": meta.get("control_id", ""),
                    "control_title": meta.get("control_title", ""),
                    "layer": meta.get("layer", "foundation"),
                })
        return all_chunks

    def cluster_concepts(self, chunks: list[dict]) -> list[ConceptCluster]:
        """Group related chunks into concept clusters by control_id and source."""
        groups: dict[str, list[dict]] = defaultdict(list)

        for chunk in chunks:
            key = chunk.get("control_id") or chunk.get("source") or "uncategorized"
            groups[key].append(chunk)

        clusters = []
        for key, group_chunks in groups.items():
            title = group_chunks[0].get("control_title") or key
            cluster = ConceptCluster(
                concept_name=title,
                slug=slugify(title, max_length=60),
                chunk_ids=[c["id"] for c in group_chunks],
                chunks=group_chunks,
                layer_sources=sorted(set(c.get("layer", "foundation") for c in group_chunks)),
            )
            clusters.append(cluster)

        clusters.sort(key=lambda c: c.concept_name)
        return clusters

    def _build_distillation_prompt(self, cluster: ConceptCluster) -> str:
        """Build the LLM prompt for distilling chunks into a wiki page."""
        chunk_texts = "\n\n---\n\n".join(
            f"[Chunk {i+1}] Source: {c.get('source', 'unknown')} | "
            f"Control: {c.get('control_id', 'N/A')}\n{c['text']}"
            for i, c in enumerate(cluster.chunks[:self.config.max_chunks_per_page])
        )

        return f"""Distill the following knowledge chunks into a single, well-structured wiki page about "{cluster.concept_name}".

Requirements:
- Use markdown with a # heading matching the concept name
- Write clear, authoritative prose (not a list of bullet points)
- Include relevant details, requirements, and examples from the source material
- Add a "## Sources" section at the end listing the source documents
- Add a "## Layer Origins" section noting which knowledge layers contributed:
  Layers present: {', '.join(cluster.layer_sources)}
- Do NOT invent information not present in the chunks
- Keep the page focused and concise (300-800 words)

Source chunks:

{chunk_texts}"""

    def generate_page(self, cluster: ConceptCluster) -> WikiPage:
        """Use LLM to distill a concept cluster into a wiki page."""
        client = self._get_anthropic()
        prompt = self._build_distillation_prompt(cluster)

        response = client.messages.create(
            model=self.config.llm_model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text

        return WikiPage(
            slug=cluster.slug,
            title=cluster.concept_name,
            content=content,
            sources=sorted(set(c.get("source", "") for c in cluster.chunks)),
            layers=cluster.layer_sources,
            chunk_ids=cluster.chunk_ids,
            generation_timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def generate_all(self) -> list[WikiPage]:
        """Full pipeline: extract -> cluster -> generate pages."""
        start = time.monotonic()
        logger.info("Starting wiki generation...")

        chunks = self.extract_chunks()
        logger.info(f"Extracted {len(chunks)} chunks from ChromaDB")
        if not chunks:
            logger.warning("No chunks found — nothing to generate")
            return []

        clusters = self.cluster_concepts(chunks)
        logger.info(f"Clustered into {len(clusters)} concepts")

        pages = []
        for i, cluster in enumerate(clusters, 1):
            logger.info(f"Generating page {i}/{len(clusters)}: {cluster.concept_name}")
            try:
                page = self.generate_page(cluster)
                pages.append(page)
            except Exception as e:
                logger.error(f"Failed to generate page for '{cluster.concept_name}': {e}")

        elapsed = time.monotonic() - start
        logger.info(f"Generated {len(pages)} pages in {elapsed:.1f}s")
        return pages
