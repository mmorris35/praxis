"""Wiki page generator — distills ChromaDB chunks into structured markdown pages."""

from core.wiki.models import WikiConfig, WikiPage, ConceptCluster


class WikiGenerator:
    """Generates wiki pages from ChromaDB knowledge chunks using LLM distillation."""

    def __init__(self, config: WikiConfig) -> None:
        self.config = config

    def extract_chunks(self) -> list[dict]:
        """Pull all chunks from the ChromaDB collection."""
        raise NotImplementedError

    def cluster_concepts(self, chunks: list[dict]) -> list[ConceptCluster]:
        """Group related chunks into concept clusters."""
        raise NotImplementedError

    def generate_page(self, cluster: ConceptCluster) -> WikiPage:
        """Use LLM to distill a concept cluster into a wiki page."""
        raise NotImplementedError

    def generate_all(self) -> list[WikiPage]:
        """Full pipeline: extract -> cluster -> generate pages."""
        raise NotImplementedError
