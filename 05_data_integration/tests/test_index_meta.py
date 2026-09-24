import os
import json
import pytest
from data_integration.index_meta import IndexMeta, load_manifest


@pytest.fixture
def mock_env(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db_dir = tmp_path / "vector_db"
    db_dir.mkdir()

    with open(data_dir / "safety.json", "w", encoding="utf-8") as f:
        json.dump({"Safety": [{"situation": "Snow", "advices": ["Stay warm"]}]}, f)

    # Fake artifacts
    for f in ["document.index", "bm25_index.pkl", "chunk_store.json"]:
        with open(db_dir / f, "w") as fp:
            fp.write("dummy artifact data")

    meta_file = db_dir / "index_meta.json"
    return str(data_dir), str(db_dir), str(meta_file)


def test_index_meta_staleness_lifecycle(mock_env):
    data_dir, db_dir, meta_file = mock_env
    meta = IndexMeta(data_dir=data_dir, meta_file=meta_file)

    # Initially stale because meta_file does not exist
    assert meta.is_stale(target_dir=db_dir) is True

    # Build manifest and update meta
    manifest = meta.build_manifest(total_chunks=1, total_sources=1, source_files=["safety.json"])
    meta.update_meta(manifest)

    # Now should not be stale
    assert meta.is_stale(target_dir=db_dir) is False

    # Modify corpus -> should become stale
    with open(os.path.join(data_dir, "safety.json"), "a", encoding="utf-8") as f:
        f.write("\n")
    assert meta.is_stale(target_dir=db_dir) is True

    # Update meta again
    new_manifest = meta.build_manifest(total_chunks=1, total_sources=1, source_files=["safety.json"])
    meta.update_meta(new_manifest)
    assert meta.is_stale(target_dir=db_dir) is False

    # Remove an artifact -> should become stale
    os.remove(os.path.join(db_dir, "document.index"))
    assert meta.is_stale(target_dir=db_dir) is True


def test_load_manifest_valid(mock_env):
    data_dir, db_dir, meta_file = mock_env
    meta = IndexMeta(data_dir=data_dir, meta_file=meta_file)
    manifest = meta.build_manifest(total_chunks=5, total_sources=2, source_files=["a.json", "b.pdf"])
    meta.update_meta(manifest)

    loaded = load_manifest(meta_file)
    assert loaded is not None
    assert loaded.total_chunks == 5
    assert loaded.total_sources == 2
    assert loaded.schema_version == "1.0.0"
