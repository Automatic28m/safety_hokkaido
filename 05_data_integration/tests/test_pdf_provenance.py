import os
import pytest
from data_integration.document_loader import load_all_data


def test_pdf_page_provenance():
    # Use real PDF from the repository data directory
    repo_data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "02_api_backend", "data")
    if not os.path.exists(repo_data_dir):
        pytest.skip("Repo data directory not found.")

    pdf_files = [f for f in os.listdir(repo_data_dir) if f.endswith(".pdf")]
    if not pdf_files:
        pytest.skip("No PDF files in data directory.")

    chunks = load_all_data(repo_data_dir)
    pdf_chunks = [c for c in chunks if c["metadata"]["source_file"].endswith(".pdf")]

    assert len(pdf_chunks) > 0

    # Ensure page is an integer >= 1 and chunk_id has p{page}
    pages_seen = set()
    for chunk in pdf_chunks:
        page = chunk["metadata"]["page"]
        assert page is not None, f"Chunk {chunk['chunk_id']} has null page"
        assert isinstance(page, int)
        assert page >= 1
        pages_seen.add(page)
        # Verify chunk_id contains the page tag
        assert f"_p{page:03d}_" in chunk["chunk_id"]

    # Verify that multi-page PDFs produced chunks with multiple distinct page numbers
    assert len(pages_seen) > 1
