import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from runtime import configure_module_paths

configure_module_paths()

from data_integration.document_loader import load_all_data
from data_integration.embedding_model import EmbeddingModel
from data_integration.vector_store import VectorStore
from data_integration.index_meta import IndexMeta
from config import config


def main():
    print("--- Checking Dataset Fingerprint ---")
    meta_path = os.path.join(config.DB_DIR, "index_meta.json")
    meta = IndexMeta(
        data_dir=config.DATA_DIR,
        meta_file=meta_path,
        chunk_settings={
            "chunk_size": getattr(config, "CHUNK_SIZE", 400),
            "chunk_overlap": getattr(config, "CHUNK_OVERLAP", 50),
        },
        embedding_model=getattr(config, "EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2"),
    )

    if not meta.is_stale(target_dir=config.DB_DIR):
        print("✅ Data has not changed since the last build. Skipping database generation to save time!")
        return
    else:
        print("⚠️ Data has changed (or this is the first run). Initiating full database build...")

    print("\n--- Phase 1: Loading & Chunking ---")
    chunks = load_all_data(config.DATA_DIR)
    if not chunks:
        print("Error: No data found in the 'data' directory!")
        return
    print(f"Loaded {len(chunks)} contextual chunks from files.")

    print("\n--- Phase 2: Generating Embeddings ---")
    print("Downloading/Loading SentenceTransformer Model...")
    embedder = EmbeddingModel()

    print("Converting text to vectors...")
    texts = [c["text"] for c in chunks]
    embeddings = embedder.encode(texts)

    print("\n--- Phase 3: Building Vector Store ---")
    store = VectorStore(config.DB_DIR)
    source_files = sorted(list({c["metadata"]["source_file"] for c in chunks}))
    manifest = meta.build_manifest(
        total_chunks=len(chunks),
        total_sources=len(source_files),
        source_files=source_files,
        embedding_model=getattr(config, "EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2"),
        chunk_settings={
            "chunk_size": getattr(config, "CHUNK_SIZE", 400),
            "chunk_overlap": getattr(config, "CHUNK_OVERLAP", 50),
        },
    )
    store.build_indexes(chunks, embeddings, manifest=manifest)

    print(f"\n✅ DONE! The RAG backend is now primed with knowledge. (Index version: {manifest.index_version})")


if __name__ == "__main__":
    main()
