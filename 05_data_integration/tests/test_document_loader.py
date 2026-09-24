import os
import json
import pytest
from pypdf import PdfWriter

from data_integration.document_loader import (
    load_all_data,
    CorpusParseError,
    CorpusValidationError,
    compute_file_sha256,
)
from data_integration.text_splitter import TextSplitter


@pytest.fixture
def sample_corpus(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # 1. Structured JSON
    json_data = {
        "Snow Hazards": [
            {
                "situation": "Whiteout on Expressway",
                "url": "https://hokkaido-safety.jp/snow",
                "advices": [
                    "Slow down and turn on hazard lamps.",
                    "Pull over into a designated parking area if safe.",
                ],
            },
            {
                "situation": "Hypothermia Symptoms",
                "advices": [
                    "Shivering, slurred speech, and exhaustion are early signs.",
                    "Move to a warm room immediately and call 119.",
                ],
            },
        ]
    }
    with open(data_dir / "snow_safety.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f)

    # 2. Golden set (must be excluded)
    golden_data = [{"query": "What to do in blizzard?", "expected": "Slow down"}]
    with open(data_dir / "golden_set.json", "w", encoding="utf-8") as f:
        json.dump(golden_data, f)

    # 3. Unstructured TXT
    txt_content = "JR Hokkaido emergency numbers: Sapporo Station 011-xxx-xxxx."
    with open(data_dir / "train_contacts.txt", "w", encoding="utf-8") as f:
        f.write(txt_content)

    # 4. Multi-page PDF
    pdf_path = data_dir / "multi_page_guide.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_blank_page(width=200, height=200)
    # pypdf blank pages don't have text streams, so we can test page reading without errors
    with open(pdf_path, "wb") as f:
        writer.write(f)

    return str(data_dir)


def test_load_all_data_excludes_golden_set(sample_corpus):
    chunks = load_all_data(sample_corpus)
    source_files = {c["metadata"]["source_file"] for c in chunks}

    assert "golden_set.json" not in source_files
    assert "snow_safety.json" in source_files
    assert "train_contacts.txt" in source_files


def test_json_loading_and_metadata(sample_corpus):
    chunks = load_all_data(sample_corpus)
    snow_chunks = [c for c in chunks if c["metadata"]["source_file"] == "snow_safety.json"]

    assert len(snow_chunks) >= 2
    for c in snow_chunks:
        assert c["chunk_id"] is not None
        assert "Topic: Snow Hazards" in c["text"]
        assert c["metadata"]["category"] == "Snow Hazards"
        assert c["metadata"]["situation"] in ["Whiteout on Expressway", "Hypothermia Symptoms"]
        assert c["metadata"]["source_version"] != ""
        assert c["metadata"]["reviewed_at"] != ""
        assert c["metadata"]["page"] is None


def test_stable_chunk_id_determinism(sample_corpus):
    chunks_run1 = load_all_data(sample_corpus)
    chunks_run2 = load_all_data(sample_corpus)

    ids1 = [c["chunk_id"] for c in chunks_run1]
    ids2 = [c["chunk_id"] for c in chunks_run2]

    assert ids1 == ids2
    assert len(set(ids1)) == len(ids1)  # All IDs must be unique


def test_invalid_json_raises_error(tmp_path):
    bad_dir = tmp_path / "bad_data"
    bad_dir.mkdir()

    with open(bad_dir / "corrupt.json", "w") as f:
        f.write("{invalid json content")

    with pytest.raises(CorpusParseError):
        load_all_data(str(bad_dir), strict=True)


def test_handles_null_fields_in_json(tmp_path):
    data_dir = tmp_path / "null_data"
    data_dir.mkdir()

    json_with_nulls = {
        "General": [
            {
                "situation": None,
                "url": None,
                "advices": ["Valid advice", None, ""],
            }
        ]
    }
    with open(data_dir / "null_test.json", "w", encoding="utf-8") as f:
        json.dump(json_with_nulls, f)

    chunks = load_all_data(str(data_dir))
    assert len(chunks) == 1
    assert chunks[0]["metadata"]["situation"] == "General"
    assert chunks[0]["metadata"]["url"] == "Local Document"
    assert "Valid advice" in chunks[0]["text"]
