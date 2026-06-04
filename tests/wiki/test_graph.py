"""Tests for knowledge graph metadata."""

import json
import pytest
from pathlib import Path
from core.wiki.models import WikiPage
from core.wiki.graph import KnowledgeGraph


@pytest.fixture
def linked_pages():
    return [
        WikiPage(slug="a", title="Concept A", content="A", layers=["foundation"], links_to=["b"], linked_from=["b"], chunk_ids=["c1"]),
        WikiPage(slug="b", title="Concept B", content="B", layers=["refinement"], links_to=["a"], linked_from=["a"], chunk_ids=["c2", "c3"]),
    ]


class TestGraphBuilder:
    def test_build_graph(self, linked_pages):
        graph = KnowledgeGraph(linked_pages).build_graph()
        assert len(graph["nodes"]) == 2
        assert len(graph["edges"]) == 2
        node_a = next(n for n in graph["nodes"] if n["id"] == "a")
        assert node_a["label"] == "Concept A"
        assert node_a["chunk_count"] == 1

    def test_build_link_map(self, linked_pages):
        lm = KnowledgeGraph(linked_pages).build_link_map()
        assert lm["a"]["link_count"] == 2
        assert "b" in lm["a"]["links_to"]

    def test_write(self, linked_pages, tmp_path):
        kg = KnowledgeGraph(linked_pages)
        kg.write(tmp_path)
        assert (tmp_path / "graph.json").exists()
        assert (tmp_path / "_meta" / "link-map.json").exists()
        graph = json.loads((tmp_path / "graph.json").read_text())
        assert len(graph["nodes"]) == 2
