from typing import List, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter

DEFAULT_CHUNK_SIZE = 400
DEFAULT_CHUNK_OVERLAP = 50


class TextSplitter:
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        if chunk_size is None or chunk_overlap is None:
            try:
                from config import config
                resolved_size = chunk_size or getattr(config, "CHUNK_SIZE", DEFAULT_CHUNK_SIZE)
                resolved_overlap = chunk_overlap or getattr(config, "CHUNK_OVERLAP", DEFAULT_CHUNK_OVERLAP)
            except Exception:
                resolved_size = chunk_size or DEFAULT_CHUNK_SIZE
                resolved_overlap = chunk_overlap or DEFAULT_CHUNK_OVERLAP
        else:
            resolved_size = chunk_size
            resolved_overlap = chunk_overlap

        self.chunk_size = resolved_size
        self.chunk_overlap = resolved_overlap

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def split_text(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []
        chunks = self.splitter.split_text(text.strip())
        return [c.strip() for c in chunks if c.strip()]
