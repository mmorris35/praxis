"""CLI commands for Praxis MCP Server."""

import click


@click.group()
def mcp():
    """MCP Server — expose knowledge base to coding agents."""
    pass


@mcp.command()
def stdio():
    """Run MCP server over stdio (for local editors like Claude Code)."""
    from core.mcp.server import mcp as mcp_server

    click.echo("Starting Praxis MCP server (stdio)...", err=True)
    mcp_server.run(transport="stdio")


@mcp.command()
@click.option("--port", "-p", default=8790, help="Port for streamable-HTTP transport.")
@click.option("--host", default="0.0.0.0", help="Host to bind to.")
def http(port: int, host: str):
    """Run MCP server over streamable-HTTP (for shared instances)."""
    from core.mcp.server import mcp as mcp_server

    click.echo(f"Starting Praxis MCP server (streamable-HTTP) on {host}:{port}...")
    mcp_server.run(transport="streamable-http", host=host, port=port)
