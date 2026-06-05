"""Incremental wiki updates — detect changes and regenerate affected pages."""

import json
import logging
import re
from pathlib import Path
from core.wiki.models import WikiConfig, WikiPage
from core.wiki.generator import WikiGenerator
from core.wiki.interlinker import WikiInterlinker
from core.wiki.writer import WikiWriter
from core.wiki.graph import KnowledgeGraph

logger = logging.getLogger("praxis.wiki")


class IncrementalUpdater:
    """Detects changes in ChromaDB and regenerates only affected wiki pages."""

    def __init__(self, config: WikiConfig, output_dir: Path, chroma_client: "chromadb.ClientAPI | None" = None) -> None:
        self.config = config
        self.output_dir = output_dir
        self.generator = WikiGenerator(config, chroma_client=chroma_client)
        self._last_gen: dict | None = None

    def _load_last_generation(self) -> dict:
        """Load the last generation log to compare against (cached per instance)."""
        if self._last_gen is not None:
            return self._last_gen
        log_path = self.output_dir / "_meta" / "generation-log.json"
        if not log_path.exists():
            self._last_gen = {"pages": []}
        else:
            self._last_gen = json.loads(log_path.read_text(encoding="utf-8"))
        return self._last_gen

    @staticmethod
    def _strip_frontmatter(text: str) -> str:
        """Remove YAML frontmatter (---...---) from the start of a file."""
        return re.sub(r"\A---\n.*?\n---\n\n?", "", text, count=1, flags=re.DOTALL)

    def _load_existing_pages(self) -> list[WikiPage]:
        """Load existing wiki pages from disk."""
        pages = []
        concepts_dir = self.output_dir / "concepts"
        if not concepts_dir.exists():
            return pages
        last_gen = self._load_last_generation()
        meta_by_slug = {p["slug"]: p for p in last_gen.get("pages", [])}
        for md_file in concepts_dir.glob("*.md"):
            slug = md_file.stem
            meta = meta_by_slug.get(slug, {})
            raw = md_file.read_text(encoding="utf-8")
            pages.append(WikiPage(
                slug=slug,
                title=meta.get("title", slug),
                content=self._strip_frontmatter(raw),
                sources=meta.get("sources", []),
                layers=meta.get("layers", []),
                chunk_ids=meta.get("chunk_ids", []),
            ))
        return pages

    def detect_changes(self, chunks: list[dict] | None = None) -> dict:
        """Compare current ChromaDB state against last generation.

        Returns dict with keys: new_chunks, deleted_chunks, affected_slugs, chunks, clusters.
        """
        last_gen = self._load_last_generation()
        last_chunk_ids: set[str] = set()
        for page_meta in last_gen.get("pages", []):
            if "chunk_ids" in page_meta:
                last_chunk_ids.update(page_meta["chunk_ids"])

        if chunks is None:
            chunks = self.generator.extract_chunks()
        current_chunk_ids = {c["id"] for c in chunks}

        new_ids = current_chunk_ids - last_chunk_ids
        deleted_ids = last_chunk_ids - current_chunk_ids

        affected_slugs = set()
        clusters = self.generator.cluster_concepts(chunks)
        for cluster in clusters:
            cluster_ids = set(cluster.chunk_ids)
            if cluster_ids & new_ids:
                affected_slugs.add(cluster.slug)

        if deleted_ids:
            for page_meta in last_gen.get("pages", []):
                old_chunk_ids = set(page_meta.get("chunk_ids", []))
                if old_chunk_ids & deleted_ids:
                    affected_slugs.add(page_meta["slug"])

        return {
            "new_chunks": len(new_ids),
            "deleted_chunks": len(deleted_ids),
            "affected_slugs": list(affected_slugs),
            "total_current_chunks": len(current_chunk_ids),
            "chunks": chunks,
            "clusters": clusters,
        }

    def update(self) -> list[str]:
        """Regenerate affected pages, re-interlink all, and update graph. Returns list of updated slugs."""
        chunks = self.generator.extract_chunks()
        changes = self.detect_changes(chunks=chunks)
        if not changes["affected_slugs"]:
            logger.info("No changes detected — wiki is up to date")
            return []

        logger.info(f"Detected {changes['new_chunks']} new, {changes['deleted_chunks']} deleted chunks")
        logger.info(f"Regenerating {len(changes['affected_slugs'])} affected pages")

        clusters = changes["clusters"]
        affected_set = set(changes["affected_slugs"])
        affected = [c for c in clusters if c.slug in affected_set]

        cluster_slugs = {c.slug for c in clusters}
        orphaned_slugs = affected_set - cluster_slugs
        concepts_dir = self.output_dir / "concepts"
        for slug in orphaned_slugs:
            orphan_path = (concepts_dir / f"{slug}.md").resolve()
            if not orphan_path.is_relative_to(concepts_dir.resolve()):
                logger.warning(f"Refusing to delete orphan outside concepts dir: {slug!r}")
                continue
            if orphan_path.exists():
                orphan_path.unlink()
                logger.info(f"Removed orphaned page: {slug}")

        new_pages = {}
        for cluster in affected:
            page = self.generator.generate_page(cluster)
            new_pages[page.slug] = page

        all_pages = self._load_existing_pages()
        all_pages = [p for p in all_pages if p.slug not in orphaned_slugs]
        all_pages = [new_pages.get(p.slug, p) for p in all_pages]
        for slug, page in new_pages.items():
            if not any(p.slug == slug for p in all_pages):
                all_pages.append(page)

        linker = WikiInterlinker(all_pages)
        all_pages = linker.interlink_all()

        writer = WikiWriter(self.output_dir)
        writer.write_all(all_pages)

        graph = KnowledgeGraph(all_pages)
        graph.write(self.output_dir)

        self._last_gen = None

        updated_slugs = list(new_pages.keys())
        logger.info(f"Updated {len(updated_slugs)} pages, re-interlinked all, rebuilt graph")
        return updated_slugs
