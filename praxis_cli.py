"""Praxis CLI — entry point for all Praxis commands."""

import click
from core.wiki.cli import wiki
from core.mcp.cli import mcp


@click.group()
@click.version_option(version="0.1.0", prog_name="praxis")
def cli():
    """Praxis — Expert system platform with RAG, AMP, Wiki Mode, and MCP Server."""
    pass


cli.add_command(wiki)
cli.add_command(mcp)


if __name__ == "__main__":
    cli()
