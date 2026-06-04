"""Tests for incremental wiki updates."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from core.wiki.models import WikiConfig, WikiPage
from core.wiki.incremental import IncrementalUpdater


@pytest.fixture
def wiki_dir(tmp_path):
    meta = tmp_path / "_meta"
    meta.mkdir()
    concepts = tmp_path / "concepts"
    concepts.mkdir()
    log = {
        "pages": [
            {"slug": "access-control", "title": "Access Control", "chunk_ids": ["c1", "c2"], "sources": ["s"], "layers": ["foundation"]},
            {"slug": "audit-logging", "title": "Audit Logging", "chunk_ids": ["c3"], "sources": ["s"], "layers": ["foundation"]},
        ]
    }
    (meta / "generation-log.json").write_text(json.dumps(log))
    (concepts / "access-control.md").write_text("# Access Control\nOld content.")
    (concepts / "audit-logging.md").write_text("# Audit Logging\nOld content.")
    return tmp_path


@pytest.fixture
def config():
    return WikiConfig(chroma_path="/tmp/test-chroma")


class TestChangeDetection:
    @patch.object(IncrementalUpdater, "_load_last_generation")
    def test_no_generation_log(self, mock_load, config, tmp_path):
        mock_load.return_value = {"pages": []}
        updater = IncrementalUpdater(config, tmp_path)
        with patch.object(updater.generator, "extract_chunks", return_value=[]):
            changes = updater.detect_changes()
            assert changes["affected_slugs"] == []

    def test_detects_new_chunks(self, config, wiki_dir):
        updater = IncrementalUpdater(config, wiki_dir)
        new_chunks = [
            {"id": "c1", "text": "t1", "source": "s", "control_id": "AC-1", "control_title": "AC", "layer": "foundation"},
            {"id": "c4", "text": "t4", "source": "s", "control_id": "AC-1", "control_title": "AC", "layer": "refinement"},
        ]
        with patch.object(updater.generator, "extract_chunks", return_value=new_chunks):
            with patch.object(updater.generator, "cluster_concepts") as mock_cluster:
                mock_cluster.return_value = [
                    MagicMock(slug="access-control", chunk_ids=["c1", "c4"])
                ]
                changes = updater.detect_changes()
                assert changes["new_chunks"] == 1
                assert "access-control" in changes["affected_slugs"]

    def test_detects_deleted_chunks(self, config, wiki_dir):
        updater = IncrementalUpdater(config, wiki_dir)
        remaining_chunks = [
            {"id": "c1", "text": "t1", "source": "s", "control_id": "AC-1", "control_title": "AC", "layer": "foundation"},
            {"id": "c2", "text": "t2", "source": "s", "control_id": "AC-1", "control_title": "AC", "layer": "foundation"},
        ]
        with patch.object(updater.generator, "extract_chunks", return_value=remaining_chunks):
            with patch.object(updater.generator, "cluster_concepts") as mock_cluster:
                mock_cluster.return_value = [
                    MagicMock(slug="access-control", chunk_ids=["c1", "c2"]),
                ]
                changes = updater.detect_changes()
                assert changes["deleted_chunks"] == 1
                assert changes["affected_slugs"] == []

    def test_no_changes_detected(self, config, wiki_dir):
        updater = IncrementalUpdater(config, wiki_dir)
        same_chunks = [
            {"id": "c1", "text": "t1", "source": "s", "control_id": "AC-1", "control_title": "AC", "layer": "foundation"},
            {"id": "c2", "text": "t2", "source": "s", "control_id": "AC-1", "control_title": "AC", "layer": "foundation"},
            {"id": "c3", "text": "t3", "source": "s", "control_id": "AU-1", "control_title": "AU", "layer": "foundation"},
        ]
        with patch.object(updater.generator, "extract_chunks", return_value=same_chunks):
            with patch.object(updater.generator, "cluster_concepts") as mock_cluster:
                mock_cluster.return_value = [
                    MagicMock(slug="access-control", chunk_ids=["c1", "c2"]),
                    MagicMock(slug="audit-logging", chunk_ids=["c3"]),
                ]
                changes = updater.detect_changes()
                assert changes["new_chunks"] == 0
                assert changes["deleted_chunks"] == 0
                assert changes["affected_slugs"] == []

    def test_affected_slugs_identified_correctly(self, config, wiki_dir):
        updater = IncrementalUpdater(config, wiki_dir)
        new_chunks = [
            {"id": "c1", "text": "t1", "source": "s", "control_id": "AC-1", "control_title": "AC", "layer": "foundation"},
            {"id": "c2", "text": "t2", "source": "s", "control_id": "AC-1", "control_title": "AC", "layer": "foundation"},
            {"id": "c4", "text": "t4", "source": "s", "control_id": "AC-1", "control_title": "AC", "layer": "refinement"},
        ]
        with patch.object(updater.generator, "extract_chunks", return_value=new_chunks):
            with patch.object(updater.generator, "cluster_concepts") as mock_cluster:
                mock_cluster.return_value = [
                    MagicMock(slug="access-control", chunk_ids=["c1", "c2", "c4"]),
                ]
                changes = updater.detect_changes()
                assert len(changes["affected_slugs"]) >= 1
                assert "access-control" in changes["affected_slugs"]

    def test_accepts_preloaded_chunks(self, config, wiki_dir):
        updater = IncrementalUpdater(config, wiki_dir)
        chunks = [
            {"id": "c1", "text": "t1", "source": "s", "control_id": "AC-1", "control_title": "AC", "layer": "foundation"},
            {"id": "c5", "text": "t5", "source": "s", "control_id": "AC-1", "control_title": "AC", "layer": "refinement"},
        ]
        with patch.object(updater.generator, "cluster_concepts") as mock_cluster:
            mock_cluster.return_value = [
                MagicMock(slug="access-control", chunk_ids=["c1", "c5"])
            ]
            changes = updater.detect_changes(chunks=chunks)
            assert changes["new_chunks"] == 1
            assert changes["deleted_chunks"] == 2


class TestIncrementalUpdate:
    def test_update_returns_updated_slugs(self, config, wiki_dir):
        updater = IncrementalUpdater(config, wiki_dir)
        new_chunks = [
            {"id": "c1", "text": "t1", "source": "s", "control_id": "AC-1", "control_title": "Access Control", "layer": "foundation"},
            {"id": "c4", "text": "t4", "source": "s", "control_id": "AC-1", "control_title": "Access Control", "layer": "refinement"},
        ]
        mock_page = WikiPage(
            slug="access-control",
            title="Access Control",
            content="# Access Control\nUpdated content.",
            layers=["foundation", "refinement"],
            chunk_ids=["c1", "c4"],
        )
        with patch.object(updater.generator, "extract_chunks", return_value=new_chunks):
            with patch.object(updater.generator, "cluster_concepts") as mock_cluster:
                with patch.object(updater.generator, "generate_page", return_value=mock_page):
                    mock_cluster.return_value = [
                        MagicMock(slug="access-control", chunk_ids=["c1", "c4"])
                    ]
                    updated = updater.update()
                    assert "access-control" in updated
                    page_file = wiki_dir / "concepts" / "access-control.md"
                    assert page_file.exists()
                    assert (wiki_dir / "index.md").exists()
                    assert (wiki_dir / "graph.json").exists()

    def test_update_no_changes(self, config, wiki_dir):
        updater = IncrementalUpdater(config, wiki_dir)
        same_chunks = [
            {"id": "c1", "text": "t1", "source": "s", "control_id": "AC-1", "control_title": "AC", "layer": "foundation"},
            {"id": "c2", "text": "t2", "source": "s", "control_id": "AC-1", "control_title": "AC", "layer": "foundation"},
            {"id": "c3", "text": "t3", "source": "s", "control_id": "AU-1", "control_title": "AU", "layer": "foundation"},
        ]
        with patch.object(updater.generator, "extract_chunks", return_value=same_chunks):
            with patch.object(updater.generator, "cluster_concepts") as mock_cluster:
                mock_cluster.return_value = [
                    MagicMock(slug="access-control", chunk_ids=["c1", "c2"]),
                    MagicMock(slug="audit-logging", chunk_ids=["c3"]),
                ]
                updated = updater.update()
                assert updated == []
