"""Tests for wiki interlinking."""

import pytest
from core.wiki.models import WikiPage
from core.wiki.interlinker import WikiInterlinker


@pytest.fixture
def sample_pages():
    return [
        WikiPage(slug="access-control", title="Access Control", content="# Access Control\n\nRequires audit logging for all access attempts."),
        WikiPage(slug="audit-logging", title="Audit Logging", content="# Audit Logging\n\nAccess control events must be logged."),
        WikiPage(slug="encryption", title="Encryption", content="# Encryption\n\nData at rest must be encrypted using AES-256."),
    ]


class TestConceptIndex:
    def test_builds_index(self, sample_pages):
        linker = WikiInterlinker(sample_pages)
        index = linker.build_concept_index()
        assert "access control" in index
        assert index["access control"] == "access-control"

    def test_case_insensitive(self, sample_pages):
        linker = WikiInterlinker(sample_pages)
        index = linker.build_concept_index()
        assert "audit logging" in index


class TestLinkInjection:
    def test_injects_wikilinks(self, sample_pages):
        linker = WikiInterlinker(sample_pages)
        linked = linker.interlink_all()
        ac_page = next(p for p in linked if p.slug == "access-control")
        assert "[[Audit Logging]]" in ac_page.content

    def test_no_self_links(self, sample_pages):
        linker = WikiInterlinker(sample_pages)
        linked = linker.interlink_all()
        ac_page = next(p for p in linked if p.slug == "access-control")
        assert "[[Access Control]]" not in ac_page.content

    def test_reverse_links_populated(self, sample_pages):
        linker = WikiInterlinker(sample_pages)
        linked = linker.interlink_all()
        audit_page = next(p for p in linked if p.slug == "audit-logging")
        assert "access-control" in audit_page.linked_from


class TestNoLinksPage:
    def test_unrelated_page_no_links(self):
        pages = [
            WikiPage(slug="a", title="Alpha", content="# Alpha\n\nNothing related."),
            WikiPage(slug="b", title="Beta", content="# Beta\n\nAlso unrelated."),
        ]
        linker = WikiInterlinker(pages)
        linked = linker.interlink_all()
        assert all(p.links_to == [] for p in linked)
