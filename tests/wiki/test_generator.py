"""Tests for wiki page generation pipeline."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from core.wiki.models import WikiConfig, WikiPage, ConceptCluster
from core.wiki.generator import WikiGenerator
from core.wiki.writer import WikiWriter


@pytest.fixture
def sample_chunks():
    return [
        {"id": "c1", "text": "Access control policy requires MFA.", "source": "800-171", "control_id": "AC-1", "control_title": "Access Control Policy", "layer": "foundation"},
        {"id": "c2", "text": "AC-1 must be reviewed annually.", "source": "800-171", "control_id": "AC-1", "control_title": "Access Control Policy", "layer": "foundation"},
        {"id": "c3", "text": "Audit logs must be retained 90 days.", "source": "800-171", "control_id": "AU-1", "control_title": "Audit and Accountability", "layer": "foundation"},
        {"id": "c4", "text": "Refinement: AC-1 also requires FIDO2 keys for admin access.", "source": "refinement", "control_id": "AC-1", "control_title": "Access Control Policy", "layer": "refinement"},
        {"id": "c5", "text": "Institutional guidance: AU-1 retention extended to 1 year for FedRAMP.", "source": "institutional", "control_id": "AU-1", "control_title": "Audit and Accountability", "layer": "institutional"},
    ]


@pytest.fixture
def config():
    return WikiConfig(chroma_path="/tmp/test-chroma", collection_name="test")


class TestConceptClustering:
    def test_clusters_by_control_id(self, config, sample_chunks):
        gen = WikiGenerator(config)
        clusters = gen.cluster_concepts(sample_chunks)
        assert len(clusters) == 2
        slugs = {c.slug for c in clusters}
        assert "access-control-policy" in slugs
        assert "audit-and-accountability" in slugs

    def test_cluster_tracks_layers(self, config, sample_chunks):
        gen = WikiGenerator(config)
        clusters = gen.cluster_concepts(sample_chunks)
        ac_cluster = next(c for c in clusters if c.slug == "access-control-policy")
        assert "foundation" in ac_cluster.layer_sources
        assert "refinement" in ac_cluster.layer_sources
        au_cluster = next(c for c in clusters if c.slug == "audit-and-accountability")
        assert "institutional" in au_cluster.layer_sources

    def test_cluster_collects_chunk_ids(self, config, sample_chunks):
        gen = WikiGenerator(config)
        clusters = gen.cluster_concepts(sample_chunks)
        ac_cluster = next(c for c in clusters if c.slug == "access-control-policy")
        assert set(ac_cluster.chunk_ids) == {"c1", "c2", "c4"}

    def test_empty_input(self, config):
        gen = WikiGenerator(config)
        assert gen.cluster_concepts([]) == []

    def test_clusters_sorted_alphabetically(self, config, sample_chunks):
        gen = WikiGenerator(config)
        clusters = gen.cluster_concepts(sample_chunks)
        names = [c.concept_name for c in clusters]
        assert names == sorted(names)


class TestWikiWriter:
    def test_write_page(self, tmp_path):
        writer = WikiWriter(tmp_path / "wiki")
        page = WikiPage(slug="test-page", title="Test Page", content="# Test\n\nHello.", sources=["s1"], layers=["foundation"])
        path = writer.write_page(page)
        assert path.exists()
        content = path.read_text()
        assert '---\ntitle: "Test Page"\nlayers: [foundation]\n---' in content
        assert "# Test\n\nHello." in content

    def test_write_index(self, tmp_path):
        writer = WikiWriter(tmp_path / "wiki")
        pages = [
            WikiPage(slug="b-page", title="B Page", content="B", layers=["foundation"]),
            WikiPage(slug="a-page", title="A Page", content="A", layers=["refinement"]),
        ]
        path = writer.write_index(pages)
        content = path.read_text()
        assert "A Page" in content
        assert "B Page" in content
        assert content.index("A Page") < content.index("B Page")

    def test_write_generation_log(self, tmp_path):
        writer = WikiWriter(tmp_path / "wiki")
        pages = [WikiPage(slug="p1", title="P1", content="c", layers=["foundation"], chunk_ids=["c1"])]
        path = writer.write_generation_log(pages)
        log = json.loads(path.read_text())
        assert log["total_pages"] == 1
        assert log["pages"][0]["slug"] == "p1"
        assert log["pages"][0]["chunk_ids"] == ["c1"]

    def test_write_all(self, tmp_path):
        writer = WikiWriter(tmp_path / "wiki")
        pages = [WikiPage(slug="concept-a", title="Concept A", content="Content A", layers=["foundation"])]
        paths = writer.write_all(pages)
        assert "concept-a" in paths
        assert "index" in paths
        assert "generation-log" in paths
