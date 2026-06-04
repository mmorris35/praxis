"""Tests for wiki page generation."""

import pytest
from core.wiki.models import WikiConfig, WikiPage, ConceptCluster
from core.wiki.generator import WikiGenerator


def test_wiki_config_defaults():
    config = WikiConfig()
    assert config.output_dir.name == "wiki"
    assert config.collection_name == "praxis"
    assert config.max_chunks_per_page == 10


def test_wiki_page_model():
    page = WikiPage(
        slug="test-concept",
        title="Test Concept",
        content="# Test Concept\n\nThis is a test.",
        sources=["source1.pdf"],
        layers=["foundation"],
    )
    assert page.slug == "test-concept"
    assert "foundation" in page.layers
    assert page.links_to == []


def test_concept_cluster_model():
    cluster = ConceptCluster(
        concept_name="Access Control",
        slug="access-control",
        chunk_ids=["chunk_1", "chunk_2"],
        layer_sources=["foundation", "institutional"],
    )
    assert cluster.slug == "access-control"
    assert len(cluster.chunk_ids) == 2
