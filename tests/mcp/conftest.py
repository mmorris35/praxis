"""Pytest configuration and global fixtures."""

import sys
from unittest.mock import MagicMock


def pytest_configure(config):
    """Configure pytest and set up mocks before any imports."""
    # Mock FastMCP before any modules try to import it
    mock_fastmcp_class = MagicMock()
    mock_instance = MagicMock()
    mock_instance.name = "Praxis"
    mock_instance.tool = lambda f: f  # Decorator passthrough
    mock_fastmcp_class.return_value = mock_instance

    sys.modules["fastmcp"] = MagicMock(FastMCP=mock_fastmcp_class)
