import os
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from data_integration.models import IndexManifest, ChunkSettings

SCHEMA_VERSION = "1.0.0"


class IndexMeta:
    def __init__(
        self,
        data_dir: str,
        meta_file: str,
        chunk_settings: Optional[Dict[str, int]] = None,
        embedding_model: Optional[str] = None,
    ):
        self.data_dir = data_dir
        self.meta_file = meta_file
        self.chunk_settings = chunk_settings or {"chunk_size": 400, "chunk_overlap": 50}
        self.embedding_model = embedding_model or "all-MiniLM-L6-v2"

    def get_dir_hash(self) -> str:
        """
        Calculates a combined cryptographic hash of all raw corpus files,
        excluding golden_set.json and sorted to ensure reproducibility.
        """
        hasher = hashlib.sha256()
        for root, _, files in os.walk(self.data_dir):
            for file in sorted(files):
                if file == "golden_set.json":
                    continue
                if file.endswith(".json") or file.endswith(".txt") or file.endswith(".pdf"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "rb") as f:
                            while buf := f.read(65536):
                                hasher.update(buf)
                    except OSError:
                        pass
        return hasher.hexdigest()

    def is_stale(
        self,
        target_dir: Optional[str] = None,
        chunk_settings: Optional[Dict[str, int]] = None,
        embedding_model: Optional[str] = None,
    ) -> bool:
        """
        Returns True if corpus changed, parameters changed, or artifacts are missing.
        """
        if not os.path.exists(self.meta_file):
            return True

        try:
            with open(self.meta_file, "r", encoding="utf-8") as f:
                saved_meta = json.load(f)
        except (json.JSONDecodeError, OSError):
            return True

        current_hash = self.get_dir_hash()
        saved_hash = saved_meta.get("corpus_hash") or saved_meta.get("data_hash")
        if current_hash != saved_hash:
            return True

        # Check parameter changes if provided
        active_settings = chunk_settings or self.chunk_settings
        saved_settings = saved_meta.get("chunk_settings")
        if saved_settings and active_settings:
            if (
                saved_settings.get("chunk_size") != active_settings.get("chunk_size")
                or saved_settings.get("chunk_overlap") != active_settings.get("chunk_overlap")
            ):
                return True

        active_model = embedding_model or self.embedding_model
        saved_model = saved_meta.get("embedding_model")
        if saved_model and active_model and saved_model != active_model:
            return True

        # Check required artifact files presence
        db_dir = target_dir or os.path.dirname(self.meta_file)
        if db_dir:
            required_files = ["document.index", "bm25_index.pkl", "chunk_store.json"]
            for rf in required_files:
                p = os.path.join(db_dir, rf)
                if not os.path.exists(p) or os.path.getsize(p) == 0:
                    return True

        return False

    def build_manifest(
        self,
        total_chunks: int,
        total_sources: int,
        source_files: Optional[List[str]] = None,
        embedding_model: Optional[str] = None,
        chunk_settings: Optional[Dict[str, int]] = None,
    ) -> IndexManifest:
        """Generates a complete immutable IndexManifest instance."""
        corpus_hash = self.get_dir_hash()
        model_name = embedding_model or self.embedding_model
        settings = chunk_settings or self.chunk_settings
        timestamp = datetime.now(timezone.utc).isoformat()
        index_version = f"idx_{corpus_hash[:10]}_{int(datetime.now(timezone.utc).timestamp())}"

        return IndexManifest(
            schema_version=SCHEMA_VERSION,
            index_version=index_version,
            corpus_hash=corpus_hash,
            embedding_model=model_name,
            chunk_settings=settings,
            build_time=timestamp,
            total_chunks=total_chunks,
            total_sources=total_sources,
            source_files=source_files or [],
        )

    def update_meta(self, manifest: Optional[IndexManifest] = None) -> None:
        """Persists index metadata and manifest atomically."""
        if manifest is None:
            corpus_hash = self.get_dir_hash()
            timestamp = datetime.now(timezone.utc).isoformat()
            data = {
                "schema_version": SCHEMA_VERSION,
                "data_hash": corpus_hash,
                "corpus_hash": corpus_hash,
                "index_version": f"idx_{corpus_hash[:10]}",
                "embedding_model": self.embedding_model,
                "chunk_settings": self.chunk_settings,
                "build_time": timestamp,
            }
        else:
            data = {
                "data_hash": manifest.corpus_hash,  # Backward compatibility
                **manifest.model_dump(),
            }

        os.makedirs(os.path.dirname(os.path.abspath(self.meta_file)), exist_ok=True)
        temp_meta = f"{self.meta_file}.tmp"
        with open(temp_meta, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_meta, self.meta_file)


def load_manifest(meta_file_path: str) -> Optional[IndexManifest]:
    """Safely loads and validates an IndexManifest from file."""
    if not os.path.exists(meta_file_path):
        return None
    try:
        with open(meta_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure corpus_hash exists if data_hash is present
        if "corpus_hash" not in data and "data_hash" in data:
            data["corpus_hash"] = data["data_hash"]
        if "index_version" not in data:
            data["index_version"] = f"legacy_{data.get('corpus_hash', 'unknown')[:8]}"
        if "total_chunks" not in data:
            data["total_chunks"] = 0
        if "total_sources" not in data:
            data["total_sources"] = 0
        if "embedding_model" not in data:
            data["embedding_model"] = "all-MiniLM-L6-v2"
        if "chunk_settings" not in data:
            data["chunk_settings"] = {"chunk_size": 400, "chunk_overlap": 50}
        if "build_time" not in data:
            data["build_time"] = datetime.now(timezone.utc).isoformat()

        return IndexManifest(**data)
    except Exception:
        return None
