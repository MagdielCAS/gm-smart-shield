import pytest
from unittest.mock import MagicMock, patch
from gm_shield.features.knowledge.service import extract_text_from_file
import pandas as pd


@pytest.fixture
def mock_file_path(tmp_path):
    return tmp_path / "test_file.txt"


def test_extract_text_txt(mock_file_path):
    mock_file_path.write_text("Hello World", encoding="utf-8")
    text = extract_text_from_file(str(mock_file_path))
    assert text == "Hello World"


def test_extract_text_csv(tmp_path):
    csv_file = tmp_path / "test.csv"
    df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
    df.to_csv(csv_file, index=False)

    text = extract_text_from_file(str(csv_file))
    assert "col1" in text
    assert "col2" in text
    assert "1" in text
    assert "a" in text


@patch("gm_shield.features.knowledge.service.OpenDataLoaderPDFLoader")
def test_extract_text_pdf(mock_loader_cls):
    """PDF extraction uses OpenDataLoaderPDFLoader with markdown format."""
    from langchain_core.documents import Document

    mock_doc = Document(page_content="# Chapter 1\n\nPDF Content in Markdown", metadata={"page": 1})
    mock_loader = MagicMock()
    mock_loader.load.return_value = [mock_doc]
    mock_loader_cls.return_value = mock_loader

    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.suffix", new_callable=lambda: ".pdf"):
        text = extract_text_from_file("dummy.pdf")
        assert "PDF Content in Markdown" in text

    # Verify the loader was configured with markdown format
    mock_loader_cls.assert_called_once_with(file_path="dummy.pdf", format="markdown")




@patch("gm_shield.features.knowledge.service.OpenDataLoaderPDFLoader")
def test_extract_pages_pdf(mock_loader_cls):
    """Pages extraction returns per-page dicts with markdown content."""
    from langchain_core.documents import Document
    from gm_shield.features.knowledge.service import extract_pages_from_file

    mock_docs = [
        Document(page_content="# Page 1 content", metadata={"page": 1}),
        Document(page_content="# Page 2 content", metadata={"page": 2}),
    ]
    mock_loader = MagicMock()
    mock_loader.load.return_value = mock_docs
    mock_loader_cls.return_value = mock_loader

    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.suffix", new_callable=lambda: ".pdf"):
        pages = extract_pages_from_file("dummy.pdf")

    assert len(pages) == 2
    assert pages[0]["page_number"] == 1
    assert "Page 1 content" in pages[0]["text"]
    mock_loader_cls.assert_called_once_with(
        file_path="dummy.pdf", format="markdown", split_pages=True
    )

def test_extract_text_unsupported(tmp_path):
    bad_file = tmp_path / "test.exe"
    bad_file.touch()
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_text_from_file(str(bad_file))


def test_extract_text_not_found():
    with pytest.raises(FileNotFoundError):
        extract_text_from_file("non_existent_file.txt")
