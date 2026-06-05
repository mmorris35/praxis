"""Praxis CLI — entry point for all Praxis commands."""

import click
from core.wiki.cli import wiki


@click.group()
@click.version_option(version="0.1.0", prog_name="praxis")
def cli():
    """Praxis — Expert system platform with RAG, AMP, and Wiki Mode."""
    pass


cli.add_command(wiki)


if __name__ == "__main__":
    cli()
