import pytest
from data_integration.text_splitter import TextSplitter


def test_text_splitter_splits_paragraphs():
    splitter = TextSplitter(chunk_size=50, chunk_overlap=10)
    long_text = "This is sentence one. This is sentence two. This is sentence three. This is sentence four."
    chunks = splitter.split_text(long_text)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) > 0


def test_text_splitter_handles_empty():
    splitter = TextSplitter()
    assert splitter.split_text("") == []
    assert splitter.split_text("   \n\n  ") == []


def test_text_splitter_defaults():
    splitter = TextSplitter()
    assert splitter.chunk_size == 400
    assert splitter.chunk_overlap == 50
