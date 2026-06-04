"""Knowledge graph — build graph.json and link-map.json from wiki pages."""

import json
from pathlib import Path
from core.wiki.models import WikiPage


class KnowledgeGraph:
    """Builds knowledge graph metadata from interlinked wiki pages."""

    def __init__(self, pages: list[WikiPage]) -> None:
        self.pages = pages

    def build_graph(self) -> dict:
        """Build graph.json with nodes and edges."""
        raise NotImplementedError

    def build_link_map(self) -> dict:
        """Build link-map.json for interlink visualization."""
        raise NotImplementedError

    def write(self, output_dir: Path) -> None:
        """Write graph.json and link-map.json to output directory."""
        raise NotImplementedError
