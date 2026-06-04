"""Tests for incremental wiki updates."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from core.wiki.models import WikiConfig
from core.wiki.incremental import IncrementalUpdater


@pytest.fixture
def wiki_dir(tmp_path):
    meta = tmp_path / "_meta"
    meta.mkdir()
    log = {
        "pages": [
            {"slug": "access-control", "chunk_ids": ["c1", "c2"]},
            {"slug": "audit-logging", "chunk_ids": ["c3"]},
        ]
    }
    (meta / "generation-log.json").write_text(json.dumps(log))
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
        # c3 from audit-logging is now missing (deleted)
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
                # No clusters have c3, so nothing is marked affected (c3 is orphaned)
                assert changes["affected_slugs"] == []

    def test_no_changes_detected(self, config, wiki_dir):
        updater = IncrementalUpdater(config, wiki_dir)
        # Same chunks as in the log
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
        # c1, c2 unchanged for AC; c3 deleted from AU; c4 new for AC
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
                # AU-1 has c3 deleted, AC-1 has c4 new
                assert len(changes["affected_slugs"]) >= 1
                assert "access-control" in changes["affected_slugs"]


class TestIncrementalUpdate:
    def test_update_returns_updated_slugs(self, config, wiki_dir):
        updater = IncrementalUpdater(config, wiki_dir)
        new_chunks = [
            {"id": "c1", "text": "t1", "source": "s", "control_id": "AC-1", "control_title": "Access Control", "layer": "foundation"},
            {"id": "c4", "text": "t4", "source": "s", "control_id": "AC-1", "control_title": "Access Control", "layer": "refinement"},
        ]
        with patch.object(updater.generator, "extract_chunks", return_value=new_chunks):
            with patch.object(updater.generator, "cluster_concepts") as mock_cluster:
                with patch.object(updater.generator, "generate_page") as mock_gen:
                    mock_cluster.return_value = [
                        MagicMock(slug="access-control", chunk_ids=["c1", "c4"])
                    ]
                    mock_page = MagicMock(slug="access-control", title="Access Control", content="# Access Control\nContent here")
                    mock_gen.return_value = mock_page

                    updated = updater.update()
                    assert "access-control" in updated
                    # Verify file was written
                    page_file = wiki_dir / "concepts" / "access-control.md"
                    assert page_file.exists()

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
