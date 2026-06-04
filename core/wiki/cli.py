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
@click.option("--no-feedback", is_flag=True, help="Skip re-ingesting wiki pages into ChromaDB.")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
def generate(output: str, collection: str, chroma_path: str, no_feedback: bool, verbose: bool):
    """Generate wiki from the current knowledge base."""
    import logging
    from core.wiki.models import WikiConfig
    from core.wiki.generator import WikiGenerator
    from core.wiki.interlinker import WikiInterlinker
    from core.wiki.writer import WikiWriter
    from core.wiki.graph import KnowledgeGraph
    from core.wiki.feedback import WikiFeedback

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = WikiConfig(
        output_dir=Path(output),
        collection_name=collection,
        chroma_path=chroma_path,
    )

    click.echo(f"Generating wiki from collection '{collection}'...")
    gen = WikiGenerator(config)
    pages = gen.generate_all()

    if not pages:
        click.echo("No knowledge chunks found — nothing to generate.")
        return

    click.echo(f"Generated {len(pages)} concept pages. Interlinking...")
    linker = WikiInterlinker(pages)
    pages = linker.interlink_all()

    click.echo("Writing wiki pages...")
    writer = WikiWriter(Path(output))
    writer.write_all(pages)

    click.echo("Building knowledge graph...")
    graph = KnowledgeGraph(pages)
    graph.write(Path(output))

    if not no_feedback:
        click.echo("Ingesting wiki pages into ChromaDB...")
        fb = WikiFeedback(config)
        fb.ingest_pages(pages)
        fb.remove_stale([p.slug for p in pages])

    click.echo(f"Done! Wiki generated at {output}/ with {len(pages)} pages.")


@wiki.command()
@click.option("--output", "-o", default="wiki", help="Wiki output directory.")
@click.option("--collection", "-c", default="praxis", help="ChromaDB collection name.")
@click.option("--chroma-path", default="data/chroma", help="Path to ChromaDB persistent storage.")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
def update(output: str, collection: str, chroma_path: str, verbose: bool):
    """Regenerate pages affected by new refinements."""
    import logging
    from core.wiki.models import WikiConfig
    from core.wiki.incremental import IncrementalUpdater

    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    config = WikiConfig(
        output_dir=Path(output),
        collection_name=collection,
        chroma_path=chroma_path,
    )

    updater = IncrementalUpdater(config, Path(output))
    updated = updater.update()

    if updated:
        click.echo(f"Updated {len(updated)} pages: {', '.join(updated)}")
    else:
        click.echo("Wiki is up to date — no changes detected.")


@wiki.command()
@click.option("--port", "-p", default=8080, help="Port for local wiki server.")
@click.option("--wiki-dir", default="wiki", help="Wiki directory to serve.")
def serve(port: int, wiki_dir: str):
    """Serve wiki locally for browsing."""
    import http.server
    import functools

    wiki_path = Path(wiki_dir)
    if not wiki_path.exists():
        click.echo(f"Wiki directory '{wiki_dir}' not found. Run 'praxis wiki generate' first.")
        return

    click.echo(f"Serving wiki from {wiki_dir}/ at http://localhost:{port}")
    click.echo("Press Ctrl+C to stop.")

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(wiki_path))
    server = http.server.HTTPServer(("localhost", port), handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        click.echo("\nStopped.")


@wiki.command(name="export")
@click.option("--format", "fmt", default="markdown", type=click.Choice(["markdown"]), help="Export format.")
@click.option("--output", "-o", default="wiki-export", help="Export output directory.")
@click.option("--wiki-dir", default="wiki", help="Source wiki directory.")
def export_wiki(fmt: str, output: str, wiki_dir: str):
    """Export wiki for distribution."""
    import shutil

    src = Path(wiki_dir)
    if not src.exists():
        click.echo(f"Wiki directory '{wiki_dir}' not found. Run 'praxis wiki generate' first.")
        return

    dst = Path(output).resolve()
    if dst == Path.home() or dst == Path("/") or dst.parent == Path("/"):
        click.echo(f"Refusing to export to '{output}' — path is too broad. Use a subdirectory.")
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

    click.echo(f"Exported wiki ({fmt}) to {output}/ ({sum(1 for _ in dst.rglob('*.md'))} files)")
