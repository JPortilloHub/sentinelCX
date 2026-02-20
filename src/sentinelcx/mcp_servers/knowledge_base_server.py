"""Knowledge Base MCP server exposing semantic search tools."""

import logging
from pathlib import Path

from fastmcp import FastMCP

from sentinelcx.config import KnowledgeBaseSettings
from sentinelcx.knowledge.search import KnowledgeSearch

_log_file = "/tmp/sentinelcx_mcp.log"
logger = logging.getLogger("mcp.knowledge")
logger.setLevel(logging.INFO)
_fh = logging.FileHandler(_log_file)
_fh.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s"))
logger.addHandler(_fh)

knowledge_mcp = FastMCP("knowledge", instructions="Knowledge base semantic search and retrieval")

_search: KnowledgeSearch | None = None
_kb_path: Path | None = None


def init_search(settings: KnowledgeBaseSettings) -> None:
    global _search, _kb_path
    _search = KnowledgeSearch(settings)
    _kb_path = Path(settings.knowledge_base_path)


def _get_search() -> KnowledgeSearch:
    if _search is None:
        raise RuntimeError("Knowledge search not initialized. Call init_search() first.")
    return _search


@knowledge_mcp.tool()
def search_knowledge_base(query: str, top_k: int = 5) -> list[dict]:
    """Search the knowledge base for documents relevant to a query.

    Uses semantic similarity to find the most relevant documentation chunks.
    Returns a list of results with text, source file, heading, and relevance score.
    """
    logger.info("search_knowledge_base CALLED — query=%s, top_k=%d", query, top_k)
    results = _get_search().search(query, top_k=top_k)
    output = [
        {
            "text": r.text,
            "source_file": r.source_file,
            "heading": r.heading,
            "score": round(r.score, 4),
        }
        for r in results
    ]
    logger.info("search_knowledge_base RESULT — %d results", len(output))
    return output


@knowledge_mcp.tool()
def get_document(file_path: str) -> str:
    """Retrieve the full content of a knowledge base document by its file path.

    The file_path should be relative to the knowledge base root directory.
    """
    logger.info("get_document CALLED — file_path=%s", file_path)
    if _kb_path is None:
        raise RuntimeError("Knowledge base path not initialized.")
    full_path = _kb_path / file_path
    if not full_path.exists():
        logger.info("get_document RESULT — not found")
        return f"Document not found: {file_path}"
    if not full_path.resolve().is_relative_to(_kb_path.resolve()):
        return "Access denied: path traversal not allowed."
    content = full_path.read_text(encoding="utf-8")
    logger.info("get_document RESULT — %d chars", len(content))
    return content


@knowledge_mcp.tool()
def list_topics() -> list[dict]:
    """List all available topics/categories in the knowledge base.

    Returns directory names and document counts for each category.
    """
    if _kb_path is None:
        raise RuntimeError("Knowledge base path not initialized.")
    topics = []
    for subdir in sorted(_kb_path.iterdir()):
        if subdir.is_dir() and not subdir.name.startswith("."):
            docs = list(subdir.rglob("*.md"))
            topics.append(
                {
                    "topic": subdir.name,
                    "document_count": len(docs),
                    "documents": [str(d.relative_to(_kb_path)) for d in docs],
                }
            )
    return topics


if __name__ == "__main__":
    init_search(KnowledgeBaseSettings())
    knowledge_mcp.run()
