"""CLI commands for Praxis Wiki Mode."""

import click
from pathlib import Path


@click.group()
def wiki():
    """Wiki Mode — generate and manage knowledge wiki."""
    pass


@wiki.command()
@click.option("--output", "-o", default="wiki", help="Output directory for wiki pages.")
@click.option("--collection", "-c", default="praxis", help="ChromaDB collection name.")
@click.option("--chroma-path", default="data/chroma", help="Path to ChromaDB persistent storage.")
def generate(output: str, collection: str, chroma_path: str):
    """Generate wiki from the current knowledge base."""
    click.echo(f"Generating wiki to {output}/ from collection '{collection}'...")
    click.echo("Not yet implemented — see Phase 1.")


@wiki.command()
@click.option("--output", "-o", default="wiki", help="Wiki output directory.")
def update(output: str):
    """Regenerate pages affected by new refinements."""
    click.echo(f"Updating wiki in {output}/...")
    click.echo("Not yet implemented — see Phase 3.")


@wiki.command()
@click.option("--port", "-p", default=8080, help="Port for local wiki server.")
@click.option("--wiki-dir", default="wiki", help="Wiki directory to serve.")
def serve(port: int, wiki_dir: str):
    """Serve wiki locally with knowledge graph visualization."""
    click.echo(f"Serving wiki from {wiki_dir}/ on http://localhost:{port}")
    click.echo("Not yet implemented — see Phase 4.")


@wiki.command(name="export")
@click.option("--format", "fmt", default="html", type=click.Choice(["html", "markdown"]), help="Export format.")
@click.option("--output", "-o", default="wiki-export", help="Export output directory.")
def export_wiki(fmt: str, output: str):
    """Export wiki as static site."""
    click.echo(f"Exporting wiki as {fmt} to {output}/...")
    click.echo("Not yet implemented — see Phase 4.")
