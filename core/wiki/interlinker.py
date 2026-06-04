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
        primaries: set[str] = set()
        for page in self.pages:
            self._slug_to_title[page.slug] = page.title
            key = page.title.lower()
            self._concept_index[key] = page.slug
            primaries.add(key)
        for page in self.pages:
            words = page.title.split()
            if len(words) > 2:
                alias = page.title.lower().removesuffix(" policy").strip()
                if alias not in primaries:
                    self._concept_index[alias] = page.slug
        return self._concept_index

    def _split_protected(self, content: str) -> list[tuple[str, bool]]:
        """Split content into (text, is_protected) segments. Protected = headings, code blocks."""
        segments: list[tuple[str, bool]] = []
        code_fence = re.compile(r"^```", re.MULTILINE)
        heading = re.compile(r"^#{1,6}\s+.*$", re.MULTILINE)

        fences = [(m.start(), m.end()) for m in code_fence.finditer(content)]
        code_ranges: list[tuple[int, int]] = []
        for i in range(0, len(fences) - 1, 2):
            line_end = content.find("\n", fences[i + 1][1])
            if line_end == -1:
                line_end = len(content)
            code_ranges.append((fences[i][0], line_end))

        heading_ranges = [(m.start(), m.end()) for m in heading.finditer(content)]
        protected = sorted(code_ranges + heading_ranges, key=lambda r: r[0])

        pos = 0
        for start, end in protected:
            if start < pos:
                continue
            if pos < start:
                segments.append((content[pos:start], False))
            segments.append((content[start:end], True))
            pos = end
        if pos < len(content):
            segments.append((content[pos:], False))

        return segments

    def inject_links(self, page: WikiPage) -> WikiPage:
        """Inject [[wikilinks]] into a page's content for mentions of other concepts."""
        if not self._concept_index:
            self.build_concept_index()

        segments = self._split_protected(page.content)
        links_to = []

        for term, target_slug in sorted(self._concept_index.items(), key=lambda x: -len(x[0])):
            if target_slug == page.slug:
                continue
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            matched = False
            for idx, (text, protected) in enumerate(segments):
                if protected:
                    continue
                if pattern.search(text):
                    target_title = self._slug_to_title.get(target_slug, term)
                    new_text = pattern.sub(f"[[{target_title}]]", text, count=1)
                    parts = re.split(r"(\[\[.*?\]\])", new_text)
                    new_segs = [(p, p.startswith("[[")) for p in parts if p]
                    segments[idx:idx+1] = new_segs
                    matched = True
                    break
            if matched:
                links_to.append(target_slug)

        content = "".join(seg for seg, _ in segments)
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
