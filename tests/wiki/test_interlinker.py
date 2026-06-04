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


class TestHeadingSafe:
    def test_no_links_in_headings(self):
        pages = [
            WikiPage(slug="access-control", title="Access Control", content="# Access Control\n\n## Overview\n\nRequires audit logging."),
            WikiPage(slug="audit-logging", title="Audit Logging", content="# Audit Logging\n\nAccess control events."),
        ]
        linker = WikiInterlinker(pages)
        linked = linker.interlink_all()
        ac_page = next(p for p in linked if p.slug == "access-control")
        for line in ac_page.content.splitlines():
            if line.startswith("#"):
                assert "[[" not in line

    def test_no_links_in_code_blocks(self):
        pages = [
            WikiPage(slug="access-control", title="Access Control", content="# AC\n\n```\naudit logging config\n```\n\nSee audit logging docs."),
            WikiPage(slug="audit-logging", title="Audit Logging", content="# Audit Logging\n\nLogging."),
        ]
        linker = WikiInterlinker(pages)
        linked = linker.interlink_all()
        ac_page = next(p for p in linked if p.slug == "access-control")
        lines = ac_page.content.splitlines()
        in_code = False
        for line in lines:
            if line.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                assert "[[" not in line


class TestAliasCollision:
    def test_alias_does_not_overwrite_primary(self):
        pages = [
            WikiPage(slug="access-control", title="Access Control", content="# Access Control\n\nSee AC policy."),
            WikiPage(slug="access-control-policy", title="Access Control Policy", content="# ACP\n\nThe policy for access control."),
        ]
        linker = WikiInterlinker(pages)
        index = linker.build_concept_index()
        assert index["access control"] == "access-control"


class TestNoLinksPage:
    def test_unrelated_page_no_links(self):
        pages = [
            WikiPage(slug="a", title="Alpha", content="# Alpha\n\nNothing related."),
            WikiPage(slug="b", title="Beta", content="# Beta\n\nAlso unrelated."),
        ]
        linker = WikiInterlinker(pages)
        linked = linker.interlink_all()
        assert all(p.links_to == [] for p in linked)
