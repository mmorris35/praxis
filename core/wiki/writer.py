"""Wiki output writer — writes generated pages to disk."""

import json
from pathlib import Path
from datetime import datetime, timezone
from core.wiki.models import WikiPage


class WikiWriter:
    """Writes wiki pages and metadata to the output directory."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.concepts_dir = output_dir / "concepts"
        self.meta_dir = output_dir / "_meta"

    def _ensure_dirs(self) -> None:
        self.concepts_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)

    def write_page(self, page: WikiPage) -> Path:
        """Write a single wiki page to concepts/<slug>.md."""
        self._ensure_dirs()
        path = (self.concepts_dir / f"{page.slug}.md").resolve()
        if not path.is_relative_to(self.concepts_dir.resolve()):
            raise ValueError(f"Slug {page.slug!r} resolves outside concepts directory")
        frontmatter = f"---\ntitle: {page.title}\nlayers: [{', '.join(page.layers)}]\n---\n\n"
        path.write_text(frontmatter + page.content, encoding="utf-8")
        return path

    def write_index(self, pages: list[WikiPage]) -> Path:
        """Generate index.md with table of contents."""
        self._ensure_dirs()
        lines = ["# Praxis Knowledge Wiki\n"]
        lines.append(f"*Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*\n")
        lines.append(f"**{len(pages)} concepts** across {self._count_layers(pages)} knowledge layers.\n")
        lines.append("## Concepts\n")

        for page in sorted(pages, key=lambda p: p.title):
            layers_badge = " ".join(f"`{l}`" for l in page.layers)
            lines.append(f"- [{page.title}](concepts/{page.slug}.md) — {layers_badge}")

        path = self.output_dir / "index.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def write_generation_log(self, pages: list[WikiPage]) -> Path:
        """Write generation-log.json with metadata."""
        self._ensure_dirs()
        log = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_pages": len(pages),
            "pages": [
                {
                    "slug": p.slug,
                    "title": p.title,
                    "sources": p.sources,
                    "layers": p.layers,
                    "chunk_ids": p.chunk_ids,
                    "chunk_count": len(p.chunk_ids),
                    "timestamp": p.generation_timestamp,
                }
                for p in pages
            ],
        }
        path = self.meta_dir / "generation-log.json"
        path.write_text(json.dumps(log, indent=2), encoding="utf-8")
        return path

    def write_all(self, pages: list[WikiPage]) -> dict[str, Path]:
        """Write all pages, index, and metadata."""
        paths = {}
        for page in pages:
            paths[page.slug] = self.write_page(page)
        paths["index"] = self.write_index(pages)
        paths["generation-log"] = self.write_generation_log(pages)
        return paths

    @staticmethod
    def _count_layers(pages: list[WikiPage]) -> int:
        all_layers = set()
        for p in pages:
            all_layers.update(p.layers)
        return len(all_layers)
