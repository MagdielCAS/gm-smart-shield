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


@patch("gm_shield.features.knowledge.service.PdfReader")
def test_extract_text_pdf(mock_pdf_reader):
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "PDF Content"
    mock_pdf_reader.return_value.pages = [mock_page]

    # We don't need a real file for mocked PDF reader, just a path that "exists"
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.suffix", new_callable=lambda: ".pdf"),
    ):
        text = extract_text_from_file("dummy.pdf")
        assert "PDF Content" in text


def test_extract_text_unsupported(tmp_path):
    bad_file = tmp_path / "test.exe"
    bad_file.touch()
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_text_from_file(str(bad_file))


def test_extract_text_not_found():
    with pytest.raises(FileNotFoundError):
        extract_text_from_file("non_existent_file.txt")
