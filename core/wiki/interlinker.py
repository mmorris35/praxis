"""Wiki interlinking — detect related concepts and inject [[wikilinks]]."""

from core.wiki.models import WikiPage


class WikiInterlinker:
    """Detects related concepts across wiki pages and injects [[wikilinks]]."""

    def __init__(self, pages: list[WikiPage]) -> None:
        self.pages = pages
        self._concept_index: dict[str, str] = {}

    def build_concept_index(self) -> dict[str, str]:
        """Build a mapping of concept names/aliases to page slugs."""
        raise NotImplementedError

    def inject_links(self, page: WikiPage) -> WikiPage:
        """Inject [[wikilinks]] into a page's content."""
        raise NotImplementedError

    def interlink_all(self) -> list[WikiPage]:
        """Interlink all pages."""
        raise NotImplementedError
