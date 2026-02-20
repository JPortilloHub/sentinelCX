"""Tests for knowledge base indexer and search."""

import pytest

from sentinelcx.config import KnowledgeBaseSettings
from sentinelcx.knowledge.indexer import KnowledgeIndexer
from sentinelcx.knowledge.search import KnowledgeSearch


@pytest.fixture
def kb_settings(tmp_path):
    kb_dir = tmp_path / "knowledge_base"
    kb_dir.mkdir()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    # Create sample markdown files
    products_dir = kb_dir / "products"
    products_dir.mkdir()
    (products_dir / "overview.md").write_text(
        "# Product Overview\n\nOur product helps teams manage support tickets.\n\n"
        "## Features\n\nTicket management, analytics, and integrations.\n"
    )

    faqs_dir = kb_dir / "faqs"
    faqs_dir.mkdir()
    (faqs_dir / "login.md").write_text(
        "# Login Issues\n\nIf you can't log in, try resetting your password.\n\n"
        "## Common Causes\n\nIncorrect email, expired password, or locked account.\n"
    )

    return KnowledgeBaseSettings(
        knowledge_base_path=str(kb_dir),
        embedding_model_name="all-MiniLM-L6-v2",
        embedding_cache_dir=str(cache_dir),
    )


class TestKnowledgeIndexer:
    def test_chunk_markdown(self, kb_settings):
        indexer = KnowledgeIndexer(kb_settings)
        text = "# Heading\n\nSome content here.\n\n## Subheading\n\nMore content."
        chunks = indexer._chunk_markdown(text, "test.md")
        assert len(chunks) >= 1
        assert all(c["source_file"] == "test.md" for c in chunks)

    def test_chunk_empty_text(self, kb_settings):
        indexer = KnowledgeIndexer(kb_settings)
        chunks = indexer._chunk_markdown("", "test.md")
        assert chunks == []

    def test_index_directory(self, kb_settings):
        indexer = KnowledgeIndexer(kb_settings)
        result = indexer.index_directory()
        assert result["files"] == 2
        assert result["chunks"] > 0

        # Verify files were created
        from pathlib import Path

        cache_dir = Path(kb_settings.embedding_cache_dir)
        assert (cache_dir / "embeddings.npy").exists()
        assert (cache_dir / "metadata.json").exists()


class TestKnowledgeSearch:
    def test_search_requires_index(self, kb_settings):
        search = KnowledgeSearch(kb_settings)
        # Clear any cached index
        search._embeddings = None
        search._metadata = None
        with pytest.raises(FileNotFoundError):
            search.search("test query")

    def test_search_after_indexing(self, kb_settings):
        # First index
        indexer = KnowledgeIndexer(kb_settings)
        indexer.index_directory()

        # Then search
        search = KnowledgeSearch(kb_settings)
        results = search.search("login issues password reset", top_k=3)
        assert len(results) > 0
        assert results[0].score > 0

    def test_search_relevance(self, kb_settings):
        indexer = KnowledgeIndexer(kb_settings)
        indexer.index_directory()

        search = KnowledgeSearch(kb_settings)
        results = search.search("login password", top_k=5)
        # The login FAQ should be more relevant than the product overview
        login_results = [r for r in results if "login" in r.source_file.lower()]
        assert len(login_results) > 0
