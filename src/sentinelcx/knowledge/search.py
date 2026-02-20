"""Semantic search over cached knowledge base embeddings."""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from sentinelcx.config import KnowledgeBaseSettings


@dataclass
class SearchResult:
    text: str
    source_file: str
    heading: str
    score: float


class KnowledgeSearch:
    def __init__(self, settings: KnowledgeBaseSettings) -> None:
        self._cache_dir = Path(settings.embedding_cache_dir)
        self._model_name = settings.embedding_model_name
        self._model: SentenceTransformer | None = None
        self._embeddings: np.ndarray | None = None
        self._metadata: list[dict] | None = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def _load_index(self) -> None:
        if self._embeddings is not None:
            return
        embeddings_path = self._cache_dir / "embeddings.npy"
        metadata_path = self._cache_dir / "metadata.json"
        if not embeddings_path.exists() or not metadata_path.exists():
            raise FileNotFoundError(f"Index not found at {self._cache_dir}. Run the indexer first.")
        self._embeddings = np.load(embeddings_path)
        with open(metadata_path) as f:
            self._metadata = json.load(f)

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Search the knowledge base for documents similar to the query."""
        self._load_index()
        model = self._get_model()

        query_embedding = model.encode(query, convert_to_numpy=True)

        # Cosine similarity
        norms = np.linalg.norm(self._embeddings, axis=1) * np.linalg.norm(query_embedding)
        norms = np.where(norms == 0, 1, norms)  # avoid division by zero
        similarities = np.dot(self._embeddings, query_embedding) / norms

        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            meta = self._metadata[idx]
            results.append(
                SearchResult(
                    text=meta["text"],
                    source_file=meta["source_file"],
                    heading=meta["heading"],
                    score=float(similarities[idx]),
                )
            )
        return results
