from typing import List, Any, Optional
import os

from .models import RetrievalResultItem, EvidenceChunk, EvidenceChunkMetadata

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None


class Reranker:
    """
    Cross-Encoder Re-ranking Engine.
    Re-scores and re-ranks retrieved candidate chunks against the user query.
    Supports fallback gracefully if model loading or inference is unavailable.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        max_length: int = 512,
    ):
        self.max_length = max_length
        self.model = None
        self.is_available = False

        if model_name is None:
            try:
                from config import config
                self.model_name = getattr(
                    config,
                    "RERANKER_MODEL_NAME",
                    "cross-encoder/ms-marco-MiniLM-L-6-v2",
                )
            except ImportError:
                self.model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
        else:
            self.model_name = model_name

        if CrossEncoder is not None:
            try:
                self.model = CrossEncoder(self.model_name, max_length=self.max_length)
                self.is_available = True
            except Exception:
                self.model = None
                self.is_available = False

    def rerank(
        self,
        query: str,
        chunks: List[Any],
        top_k: Optional[int] = None,
    ) -> List[Any]:
        """
        Reranks input chunks based on query relevance using CrossEncoder.
        Maintains backward compatibility: chunks can be RetrievalResultItem or raw dicts.
        """
        if not chunks:
            return []

        k = top_k or len(chunks)

        # Fallback if cross-encoder model is not initialized
        if not self.is_available or self.model is None:
            return chunks[:k]

        # Extract text content from items
        pairs = []
        for c in chunks:
            if isinstance(c, dict):
                text = str(c.get("text", ""))
            elif hasattr(c, "chunk") and hasattr(c.chunk, "text"):
                text = str(c.chunk.text)
            elif hasattr(c, "text"):
                text = str(c.text)
            else:
                text = str(c)
            pairs.append([query, text])

        try:
            scores = self.model.predict(pairs)
        except Exception:
            return chunks[:k]

        scored_pairs = list(zip(chunks, scores))
        scored_pairs.sort(key=lambda x: x[1], reverse=True)

        selected = scored_pairs[:k]

        # Update rank and score on items
        results = []
        for rank, (item, raw_score) in enumerate(selected, start=1):
            score_val = round(float(raw_score), 4)
            if isinstance(item, RetrievalResultItem):
                item.score = score_val
                item.rank = rank
                item.retrieval_method = "hybrid+rerank"
                results.append(item)
            elif isinstance(item, dict):
                enriched = dict(item)
                enriched["score"] = score_val
                enriched["rank"] = rank
                enriched["retrieval_method"] = "hybrid+rerank"
                results.append(enriched)
            else:
                results.append(item)

        return results
