import os
import json
import pytest

from data_integration.builder import run_index_build
from data_integration.vector_store import VectorStore


def test_run_index_build_pipeline(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db_dir = tmp_path / "vector_db"

    # Create test corpus
    doc = {
        "Earthquake Safety": [
            {
                "situation": "Strong Tremor in Sapporo",
                "url": "https://safety.hokkaido.jp",
                "advices": [
                    "Drop, Cover, and Hold On under a sturdy table.",
                    "Protect your head from falling objects.",
                ],
            }
        ]
    }
    with open(data_dir / "earthquake.json", "w", encoding="utf-8") as f:
        json.dump(doc, f)

    # 1. Run build
    result = run_index_build(
        data_dir=str(data_dir),
        db_dir=str(db_dir),
        show_progress=False,
    )

    assert result.success is True
    assert result.skipped is False
    assert result.total_chunks > 0
    assert result.total_sources == 1
    assert result.manifest is not None

    store = VectorStore(db_dir=str(db_dir))
    assert store.is_ready()

    # 2. Re-run build without changes -> should skip!
    re_result = run_index_build(
        data_dir=str(data_dir),
        db_dir=str(db_dir),
        show_progress=False,
    )
    assert re_result.success is True
    assert re_result.skipped is True
