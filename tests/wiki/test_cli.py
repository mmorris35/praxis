"""CLI integration tests for wiki commands."""

import pytest
from click.testing import CliRunner
from core.wiki.cli import wiki


@pytest.fixture
def runner():
    return CliRunner()


class TestCLIHelp:
    def test_wiki_help(self, runner):
        result = runner.invoke(wiki, ["--help"])
        assert result.exit_code == 0
        assert "generate" in result.output
        assert "update" in result.output
        assert "serve" in result.output
        assert "export" in result.output

    def test_generate_help(self, runner):
        result = runner.invoke(wiki, ["generate", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output
        assert "--collection" in result.output
        assert "--no-feedback" in result.output

    def test_update_help(self, runner):
        result = runner.invoke(wiki, ["update", "--help"])
        assert result.exit_code == 0

    def test_export_help(self, runner):
        result = runner.invoke(wiki, ["export", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output


class TestServeCommand:
    def test_serve_missing_wiki_dir(self, runner):
        result = runner.invoke(wiki, ["serve", "--wiki-dir", "/nonexistent"])
        assert "not found" in result.output
        assert result.exit_code == 0


class TestExportCommand:
    def test_export_missing_wiki_dir(self, runner):
        result = runner.invoke(wiki, ["export", "--wiki-dir", "/nonexistent"])
        assert "not found" in result.output

    def test_export_copies_wiki(self, runner, tmp_path):
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir()
        (wiki_dir / "index.md").write_text("# Index")
        concepts = wiki_dir / "concepts"
        concepts.mkdir()
        (concepts / "test.md").write_text("# Test")

        export_dir = tmp_path / "export"
        result = runner.invoke(wiki, ["export", "--wiki-dir", str(wiki_dir), "-o", str(export_dir)])
        assert result.exit_code == 0
        assert (export_dir / "index.md").exists()
        assert (export_dir / "concepts" / "test.md").exists()
