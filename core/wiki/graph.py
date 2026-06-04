"""Knowledge graph — build graph.json and link-map.json from wiki pages."""

import json
from pathlib import Path
from core.wiki.models import WikiPage


class KnowledgeGraph:
    """Builds knowledge graph metadata from interlinked wiki pages."""

    def __init__(self, pages: list[WikiPage]) -> None:
        self.pages = pages

    def build_graph(self) -> dict:
        """Build graph.json with nodes and edges for visualization."""
        nodes = []
        edges = []
        for page in self.pages:
            nodes.append({
                "id": page.slug,
                "label": page.title,
                "layers": page.layers,
                "chunk_count": len(page.chunk_ids),
            })
            for target in page.links_to:
                edges.append({
                    "source": page.slug,
                    "target": target,
                })
        return {"nodes": nodes, "edges": edges}

    def build_link_map(self) -> dict:
        """Build link-map.json for interlink visualization."""
        link_map = {}
        for page in self.pages:
            link_map[page.slug] = {
                "title": page.title,
                "links_to": page.links_to,
                "linked_from": page.linked_from,
                "link_count": len(page.links_to) + len(page.linked_from),
            }
        return link_map

    def write(self, output_dir: Path) -> None:
        """Write graph.json and link-map.json to output directory."""
        meta_dir = output_dir / "_meta"
        meta_dir.mkdir(parents=True, exist_ok=True)

        graph_path = output_dir / "graph.json"
        graph_path.write_text(json.dumps(self.build_graph(), indent=2), encoding="utf-8")

        link_map_path = meta_dir / "link-map.json"
        link_map_path.write_text(json.dumps(self.build_link_map(), indent=2), encoding="utf-8")
