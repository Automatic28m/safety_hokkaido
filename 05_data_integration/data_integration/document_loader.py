import os
import re
import json
import glob
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from data_integration.text_splitter import TextSplitter
from data_integration.models import DocumentChunk, ChunkMetadata

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


class CorpusError(Exception):
    """Base exception for corpus processing errors."""
    pass


class CorpusParseError(CorpusError):
    """Raised when a corpus file is malformed or unreadable."""
    pass


class CorpusValidationError(CorpusError):
    """Raised when corpus structure violates safety requirements."""
    pass


def compute_file_sha256(file_path: str) -> str:
    """Computes SHA-256 fingerprint for a raw file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_file_reviewed_at(file_path: str) -> str:
    """Gets ISO formatted modification timestamp for traceability."""
    mtime = os.path.getmtime(file_path)
    return datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()


def sanitize_identifier(text: str) -> str:
    """Creates a URL-safe, deterministic alphanumeric identifier."""
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "_", text).strip("_")
    return cleaned.lower() if cleaned else "doc"


def load_all_data(
    data_dir: str,
    strict: bool = True,
    splitter: Optional[TextSplitter] = None,
) -> List[Dict[str, Any]]:
    """
    Ingests vetted JSON, TXT, and PDF files from data_dir.
    Ensures PDF page provenance, deterministic stable chunk IDs,
    rich metadata traceability, and strict data validation.
    """
    if not os.path.exists(data_dir):
        raise CorpusError(f"Data directory '{data_dir}' does not exist.")

    if splitter is None:
        splitter = TextSplitter()

    # Discover and sort files deterministically
    all_files: List[str] = []
    for ext in ["*.json", "*.txt", "*.pdf"]:
        all_files.extend(glob.glob(os.path.join(data_dir, ext)))
    all_files = sorted(all_files)

    chunks: List[Dict[str, Any]] = []

    for file_path in all_files:
        filename = os.path.basename(file_path)
        stem = Path(file_path).stem
        clean_stem = sanitize_identifier(stem)

        # Exclude evaluation test set
        if filename == "golden_set.json":
            continue

        try:
            file_version = compute_file_sha256(file_path)[:16]
            reviewed_at = get_file_reviewed_at(file_path)
        except Exception as e:
            if strict:
                raise CorpusParseError(f"Cannot access file '{filename}': {e}") from e
            continue

        # --- 1. Handle Structured JSON ---
        if filename.endswith(".json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                raise CorpusParseError(f"Corrupt JSON in '{filename}': {e}") from e

            if not isinstance(data, dict):
                if strict:
                    raise CorpusValidationError(
                        f"Expected JSON root dict in '{filename}', got {type(data).__name__}"
                    )
                continue

            for category, situations in data.items():
                cat_name = str(category or "General").strip()
                if not isinstance(situations, list):
                    continue

                for sit_idx, sit in enumerate(situations):
                    if not isinstance(sit, dict):
                        continue

                    situation_name = str(sit.get("situation") or "General").strip()
                    url = str(sit.get("url") or "Local Document").strip()
                    raw_advices = sit.get("advices") or []

                    if not isinstance(raw_advices, list):
                        continue

                    valid_advices = [
                        str(a).strip() for a in raw_advices if a and str(a).strip()
                    ]
                    if not valid_advices:
                        continue

                    context_header = f"Topic: {cat_name}. Situation: {situation_name}. Advice: "
                    combined_text = context_header + " ".join(valid_advices)

                    split_texts = splitter.split_text(combined_text)
                    sit_hash = hashlib.md5(
                        f"{cat_name}:{situation_name}:{sit_idx}".encode("utf-8")
                    ).hexdigest()[:8]

                    for c_idx, split_text in enumerate(split_texts):
                        chunk_id = f"{clean_stem}_{sit_hash}_c{c_idx:03d}"
                        chunk_model = DocumentChunk(
                            chunk_id=chunk_id,
                            text=split_text,
                            metadata=ChunkMetadata(
                                source_file=filename,
                                category=cat_name,
                                situation=situation_name,
                                url=url,
                                page=None,
                                source_version=file_version,
                                reviewed_at=reviewed_at,
                            ),
                        )
                        chunks.append(chunk_model.to_dict())

        # --- 2. Handle Unstructured TXT ---
        elif filename.endswith(".txt"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    raw_text = f.read()
            except Exception as e:
                raise CorpusParseError(f"Failed to read text file '{filename}': {e}") from e

            if not raw_text.strip():
                continue

            split_texts = splitter.split_text(raw_text)
            for c_idx, split_text in enumerate(split_texts):
                chunk_id = f"{clean_stem}_c{c_idx:03d}"
                chunk_model = DocumentChunk(
                    chunk_id=chunk_id,
                    text=split_text,
                    metadata=ChunkMetadata(
                        source_file=filename,
                        category="Unstructured Text",
                        situation="General Context",
                        url="Local Document",
                        page=None,
                        source_version=file_version,
                        reviewed_at=reviewed_at,
                    ),
                )
                chunks.append(chunk_model.to_dict())

        # --- 3. Handle Paginated PDF ---
        elif filename.endswith(".pdf"):
            if PdfReader is None:
                raise CorpusError(
                    f"Skipping '{filename}' - 'pypdf' package is not installed."
                )

            try:
                reader = PdfReader(file_path)
            except Exception as e:
                raise CorpusParseError(f"Failed to open PDF '{filename}': {e}") from e

            if len(reader.pages) == 0:
                if strict:
                    raise CorpusValidationError(f"PDF '{filename}' contains 0 pages.")
                continue

            for page_idx, page in enumerate(reader.pages, start=1):
                try:
                    page_text = page.extract_text() or ""
                except Exception as e:
                    if strict:
                        raise CorpusParseError(
                            f"Failed to extract page {page_idx} of '{filename}': {e}"
                        ) from e
                    continue

                cleaned_page_text = page_text.strip()
                if not cleaned_page_text:
                    continue

                split_texts = splitter.split_text(cleaned_page_text)
                for c_idx, split_text in enumerate(split_texts):
                    chunk_id = f"{clean_stem}_p{page_idx:03d}_c{c_idx:03d}"
                    chunk_model = DocumentChunk(
                        chunk_id=chunk_id,
                        text=split_text,
                        metadata=ChunkMetadata(
                            source_file=filename,
                            category="Unstructured PDF",
                            situation="General Context",
                            url="Local Document",
                            page=page_idx,
                            source_version=file_version,
                            reviewed_at=reviewed_at,
                        ),
                    )
                    chunks.append(chunk_model.to_dict())

    return chunks
