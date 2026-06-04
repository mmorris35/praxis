"""Wiki interlinking — detect related concepts and inject [[wikilinks]]."""

import re
from core.wiki.models import WikiPage


class WikiInterlinker:
    """Detects related concepts across wiki pages and injects [[wikilinks]]."""

    def __init__(self, pages: list[WikiPage]) -> None:
        self.pages = pages
        self._concept_index: dict[str, str] = {}
        self._slug_to_title: dict[str, str] = {}

    def build_concept_index(self) -> dict[str, str]:
        """Build a mapping of concept names/aliases to page slugs."""
        self._concept_index = {}
        self._slug_to_title = {}
        for page in self.pages:
            self._slug_to_title[page.slug] = page.title
            self._concept_index[page.title.lower()] = page.slug
            words = page.title.split()
            if len(words) > 2:
                self._concept_index[page.title.lower().removesuffix(" policy").strip()] = page.slug
        return self._concept_index

    def inject_links(self, page: WikiPage) -> WikiPage:
        """Inject [[wikilinks]] into a page's content for mentions of other concepts."""
        if not self._concept_index:
            self.build_concept_index()

        content = page.content
        links_to = []

        for term, target_slug in sorted(self._concept_index.items(), key=lambda x: -len(x[0])):
            if target_slug == page.slug:
                continue
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            if pattern.search(content):
                target_title = self._slug_to_title.get(target_slug, term)
                content = pattern.sub(f"[[{target_title}]]", content, count=1)
                links_to.append(target_slug)

        return WikiPage(
            slug=page.slug,
            title=page.title,
            content=content,
            sources=page.sources,
            layers=page.layers,
            links_to=links_to,
            linked_from=page.linked_from,
            chunk_ids=page.chunk_ids,
            generation_timestamp=page.generation_timestamp,
        )

    def interlink_all(self) -> list[WikiPage]:
        """Interlink all pages and compute reverse links."""
        self.build_concept_index()
        linked_pages = [self.inject_links(p) for p in self.pages]

        reverse: dict[str, list[str]] = {p.slug: [] for p in linked_pages}
        for page in linked_pages:
            for target in page.links_to:
                if target in reverse:
                    reverse[target].append(page.slug)

        for page in linked_pages:
            page.linked_from = reverse.get(page.slug, [])

        return linked_pages
