"""Incremental wiki updates — detect changes and regenerate affected pages."""

import json
import logging
from pathlib import Path
from core.wiki.models import WikiConfig
from core.wiki.generator import WikiGenerator

logger = logging.getLogger("praxis.wiki")


class IncrementalUpdater:
    """Detects changes in ChromaDB and regenerates only affected wiki pages."""

    def __init__(self, config: WikiConfig, output_dir: Path) -> None:
        self.config = config
        self.output_dir = output_dir
        self.generator = WikiGenerator(config)

    def _load_last_generation(self) -> dict:
        """Load the last generation log to compare against."""
        log_path = self.output_dir / "_meta" / "generation-log.json"
        if not log_path.exists():
            return {"pages": []}
        return json.loads(log_path.read_text(encoding="utf-8"))

    def detect_changes(self) -> dict:
        """Compare current ChromaDB state against last generation.

        Returns dict with keys: new_chunks, modified_chunks, deleted_chunks, affected_slugs.
        """
        last_gen = self._load_last_generation()
        last_chunk_ids: set[str] = set()
        for page_meta in last_gen.get("pages", []):
            if "chunk_ids" in page_meta:
                last_chunk_ids.update(page_meta["chunk_ids"])

        current_chunks = self.generator.extract_chunks()
        current_chunk_ids = {c["id"] for c in current_chunks}

        new_ids = current_chunk_ids - last_chunk_ids
        deleted_ids = last_chunk_ids - current_chunk_ids

        affected_slugs = set()
        clusters = self.generator.cluster_concepts(current_chunks)
        for cluster in clusters:
            cluster_ids = set(cluster.chunk_ids)
            if cluster_ids & (new_ids | deleted_ids):
                affected_slugs.add(cluster.slug)

        return {
            "new_chunks": len(new_ids),
            "deleted_chunks": len(deleted_ids),
            "affected_slugs": list(affected_slugs),
            "total_current_chunks": len(current_chunk_ids),
        }

    def update(self) -> list[str]:
        """Regenerate only affected pages. Returns list of updated slugs."""
        changes = self.detect_changes()
        if not changes["affected_slugs"]:
            logger.info("No changes detected — wiki is up to date")
            return []

        logger.info(f"Detected {changes['new_chunks']} new, {changes['deleted_chunks']} deleted chunks")
        logger.info(f"Regenerating {len(changes['affected_slugs'])} affected pages")

        chunks = self.generator.extract_chunks()
        clusters = self.generator.cluster_concepts(chunks)
        affected = [c for c in clusters if c.slug in changes["affected_slugs"]]

        updated_slugs = []
        for cluster in affected:
            page = self.generator.generate_page(cluster)
            page_path = self.output_dir / "concepts" / f"{page.slug}.md"
            page_path.parent.mkdir(parents=True, exist_ok=True)
            page_path.write_text(page.content, encoding="utf-8")
            updated_slugs.append(page.slug)
            logger.info(f"Updated: {page.title}")

        return updated_slugs
