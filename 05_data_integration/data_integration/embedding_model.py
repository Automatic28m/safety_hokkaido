from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class EmbeddingModel:
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
    ):
        if model_name is None:
            try:
                from config import config
                resolved_name = getattr(config, "EMBEDDING_MODEL_NAME", DEFAULT_EMBEDDING_MODEL)
            except Exception:
                resolved_name = DEFAULT_EMBEDDING_MODEL
        else:
            resolved_name = model_name

        self.model_name = resolved_name
        self.device = device
        self.model = SentenceTransformer(self.model_name, device=self.device)

    @property
    def dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()

    def encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress_bar: bool = True,
        normalize_embeddings: bool = False,
    ) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dimension), dtype="float32")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            normalize_embeddings=normalize_embeddings,
        )
        return np.array(embeddings, dtype="float32")
