"""Tests for Praxis MCP server."""

import pytest
from unittest.mock import patch, MagicMock


class TestKnowledgeSearch:
    @patch("core.gateway.rag.retrieve")
    @patch("core.gateway.rag.format_context")
    @patch("core.gateway.rag.extract_sources")
    def test_basic_search(self, mock_extract, mock_format, mock_retrieve):
        from core.mcp.server import knowledge_search

        mock_retrieve.return_value = [
            {"id": "c1", "text": "test", "source": "s1", "section": "sec",
             "control_id": "AC-1", "control_title": "Access Control", "distance": 0.1}
        ]
        mock_format.return_value = "[Source 1] s1 — sec\ntest"
        mock_extract.return_value = [{"source": "s1", "section": "sec", "control_id": "AC-1", "control_title": "Access Control", "page": ""}]

        result = knowledge_search("access control", top_k=5)
        assert "context" in result
        assert "sources" in result
        mock_retrieve.assert_called_once_with("access control", top_k=5)

    @patch("core.gateway.rag.retrieve")
    @patch("core.gateway.rag.format_context")
    @patch("core.gateway.rag.extract_sources")
    def test_top_k_capped_at_25(self, mock_extract, mock_format, mock_retrieve):
        from core.mcp.server import knowledge_search

        mock_retrieve.return_value = []
        knowledge_search("test", top_k=100)
        mock_retrieve.assert_called_once_with("test", top_k=25)

    @patch("core.gateway.rag.retrieve")
    @patch("core.gateway.rag.format_context")
    @patch("core.gateway.rag.extract_sources")
    def test_top_k_minimum_1(self, mock_extract, mock_format, mock_retrieve):
        from core.mcp.server import knowledge_search

        mock_retrieve.return_value = []
        knowledge_search("test", top_k=0)
        mock_retrieve.assert_called_once_with("test", top_k=1)

    @patch("core.gateway.rag.retrieve")
    def test_query_truncated(self, mock_retrieve):
        from core.mcp.server import knowledge_search

        mock_retrieve.return_value = []
        long_query = "x" * 3000
        knowledge_search(long_query)
        actual_query = mock_retrieve.call_args[0][0]
        assert len(actual_query) == 2000

    @patch("core.gateway.rag.retrieve")
    @patch("core.gateway.rag.format_context")
    @patch("core.gateway.rag.extract_sources")
    def test_empty_results(self, mock_extract, mock_format, mock_retrieve):
        from core.mcp.server import knowledge_search

        mock_retrieve.return_value = []
        result = knowledge_search("nonexistent topic")
        assert "No relevant results" in result["context"]
        assert result["sources"] == []

    @patch("core.gateway.rag.retrieve", side_effect=Exception("ChromaDB connection failed"))
    def test_chromadb_error_handled(self, mock_retrieve):
        from core.mcp.server import knowledge_search

        result = knowledge_search("test")
        assert result.get("error") is True
        assert "failed" in result["context"].lower()


class TestListDomains:
    @patch("core.gateway.rag._load_config")
    def test_returns_config(self, mock_config):
        from core.mcp.server import list_domains

        mock_config.return_value = {"rag": {"collection": "cmmc", "chroma_path": "data/chroma"}}
        result = list_domains()
        assert result["collection"] == "cmmc"


class TestServerSetup:
    def test_server_name(self):
        from core.mcp.server import mcp
        assert mcp.name == "Praxis"
