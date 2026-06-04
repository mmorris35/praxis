"""Tests for wiki-to-ChromaDB feedback loop."""

import pytest
from unittest.mock import MagicMock, patch
from core.wiki.models import WikiConfig, WikiPage
from core.wiki.feedback import WikiFeedback


@pytest.fixture
def config():
    return WikiConfig(chroma_path="/tmp/test-chroma")


@pytest.fixture
def sample_pages():
    return [
        WikiPage(slug="access-control", title="Access Control", content="# Access Control\nMFA required.", layers=["foundation", "refinement"]),
        WikiPage(slug="audit-logging", title="Audit Logging", content="# Audit Logging\nRetain 90 days.", layers=["foundation"]),
    ]


@pytest.fixture
def mock_collection():
    col = MagicMock()
    col.upsert = MagicMock()
    col.get = MagicMock(return_value={"ids": []})
    col.delete = MagicMock()
    return col


@pytest.fixture
def feedback(config, mock_collection):
    fb = WikiFeedback(config)
    fb._collection = mock_collection
    return fb


class TestIngestPages:
    def test_upserts_all_pages(self, feedback, sample_pages, mock_collection):
        count = feedback.ingest_pages(sample_pages)
        assert count == 2
        mock_collection.upsert.assert_called_once()
        call_args = mock_collection.upsert.call_args
        assert len(call_args.kwargs["ids"]) == 2
        assert "wiki:access-control" in call_args.kwargs["ids"]
        assert "wiki:audit-logging" in call_args.kwargs["ids"]

    def test_metadata_includes_layers(self, feedback, sample_pages, mock_collection):
        feedback.ingest_pages(sample_pages)
        call_args = mock_collection.upsert.call_args
        metadatas = call_args.kwargs["metadatas"]
        assert metadatas[0]["source"] == "wiki"
        assert metadatas[0]["layer"] == "wiki-generated"
        assert metadatas[0]["wiki_layers"] == "foundation,refinement"

    def test_empty_pages(self, feedback, mock_collection):
        count = feedback.ingest_pages([])
        assert count == 0
        mock_collection.upsert.assert_called_once()


class TestRemoveStale:
    def test_removes_stale_entries(self, feedback, mock_collection):
        mock_collection.get.return_value = {"ids": ["wiki:access-control", "wiki:old-page", "wiki:another-old"]}
        removed = feedback.remove_stale(["access-control"])
        assert removed == 2
        mock_collection.delete.assert_called_once()
        deleted_ids = set(mock_collection.delete.call_args.kwargs["ids"])
        assert deleted_ids == {"wiki:old-page", "wiki:another-old"}

    def test_no_stale_entries(self, feedback, mock_collection):
        mock_collection.get.return_value = {"ids": ["wiki:access-control"]}
        removed = feedback.remove_stale(["access-control"])
        assert removed == 0
        mock_collection.delete.assert_not_called()

    def test_all_stale(self, feedback, mock_collection):
        mock_collection.get.return_value = {"ids": ["wiki:old-a", "wiki:old-b"]}
        removed = feedback.remove_stale(["new-page"])
        assert removed == 2
