"""Knowledge base indexer using sentence-transformers for local embeddings."""

import json
import re
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from sentinelcx.config import KnowledgeBaseSettings


class KnowledgeIndexer:
    def __init__(self, settings: KnowledgeBaseSettings) -> None:
        self._kb_path = Path(settings.knowledge_base_path)
        self._cache_dir = Path(settings.embedding_cache_dir)
        self._model_name = settings.embedding_model_name
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def _chunk_markdown(self, text: str, source_file: str) -> list[dict]:
        """Split markdown by headings into chunks."""
        chunks = []
        # Split on markdown headings (##, ###, etc.)
        sections = re.split(r"(?=^#{1,4}\s)", text, flags=re.MULTILINE)

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Extract heading if present
            heading_match = re.match(r"^(#{1,4})\s+(.+?)$", section, re.MULTILINE)
            heading = heading_match.group(2).strip() if heading_match else ""

            # Skip very short chunks (likely just a heading with no content)
            if len(section) < 20:
                continue

            chunks.append(
                {
                    "text": section,
                    "source_file": source_file,
                    "heading": heading,
                }
            )

        # If no headings found, treat entire file as one chunk
        if not chunks and len(text.strip()) >= 20:
            chunks.append(
                {
                    "text": text.strip(),
                    "source_file": source_file,
                    "heading": "",
                }
            )

        return chunks

    def index_directory(self) -> dict:
        """Index all markdown files in the knowledge base directory."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        model = self._get_model()

        all_chunks = []
        for md_file in sorted(self._kb_path.rglob("*.md")):
            relative_path = str(md_file.relative_to(self._kb_path))
            text = md_file.read_text(encoding="utf-8")
            chunks = self._chunk_markdown(text, relative_path)
            all_chunks.extend(chunks)

        if not all_chunks:
            return {"chunks": 0, "files": 0}

        # Compute embeddings
        texts = [c["text"] for c in all_chunks]
        embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

        # Save embeddings and metadata
        np.save(self._cache_dir / "embeddings.npy", embeddings)
        metadata = [
            {"source_file": c["source_file"], "heading": c["heading"], "text": c["text"]}
            for c in all_chunks
        ]
        with open(self._cache_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        return {"chunks": len(all_chunks), "files": len(set(c["source_file"] for c in all_chunks))}


if __name__ == "__main__":
    settings = KnowledgeBaseSettings()
    indexer = KnowledgeIndexer(settings)
    result = indexer.index_directory()
    print(f"Indexed {result['chunks']} chunks from {result['files']} files")
