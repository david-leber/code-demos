"""Tests for PDF converter."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from resume_to_latex.pdf_converter import PDFConverter


class TestPDFConverterInit:
    """Test PDF converter initialization."""

    def test_init_with_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            PDFConverter("/path/to/nonexistent.pdf")


class TestTextBlockExtraction:
    """Test text block extraction from PDF."""

    @patch('resume_to_latex.pdf_converter.fitz.open')
    def test_extract_text_blocks(self, mock_fitz_open):
        # Mock PDF document
        mock_doc = MagicMock()
        mock_page = MagicMock()

        # Mock text blocks structure
        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "type": 0,  # Text block
                    "lines": [
                        {
                            "spans": [
                                {"text": "John Smith", "size": 16.0}
                            ]
                        }
                    ]
                },
                {
                    "type": 0,
                    "lines": [
                        {
                            "spans": [
                                {"text": "Software Engineer", "size": 12.0}
                            ]
                        }
                    ]
                }
            ]
        }

        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz_open.return_value = mock_doc

        # Create a temporary file for testing
        with patch('pathlib.Path.exists', return_value=True):
            converter = PDFConverter("test.pdf")
            blocks = converter.extract_text_blocks()

        assert len(blocks) == 2
        assert blocks[0][0] == "John Smith"
        assert blocks[0][1]["font_size"] == 16.0
        assert blocks[1][0] == "Software Engineer"


class TestStructureAnalysis:
    """Test document structure analysis."""

    @patch('pathlib.Path.exists', return_value=True)
    def test_analyze_structure_with_name(self, mock_exists):
        converter = PDFConverter("test.pdf")

        blocks = [
            ("John Smith", {"font_size": 16.0, "page": 0}),
            ("john@email.com", {"font_size": 11.0, "page": 0}),
            ("EXPERIENCE", {"font_size": 14.0, "page": 0}),
            ("Software Engineer", {"font_size": 11.0, "page": 0}),
        ]

        structured = converter.analyze_structure(blocks)

        assert structured[0]["type"] == "name"
        assert structured[0]["content"] == "John Smith"

    @patch('pathlib.Path.exists', return_value=True)
    def test_analyze_structure_with_contact_info(self, mock_exists):
        converter = PDFConverter("test.pdf")

        blocks = [
            ("john@email.com | 555-1234", {"font_size": 11.0, "page": 0}),
        ]

        structured = converter.analyze_structure(blocks)

        assert structured[0]["type"] == "contact"

    @patch('pathlib.Path.exists', return_value=True)
    def test_analyze_structure_with_section(self, mock_exists):
        converter = PDFConverter("test.pdf")

        blocks = [
            ("EDUCATION", {"font_size": 14.0, "page": 0}),
            ("Bachelor's Degree", {"font_size": 11.0, "page": 0}),
        ]

        structured = converter.analyze_structure(blocks)

        assert structured[0]["type"] == "section"
        assert structured[0]["content"] == "EDUCATION"

    @patch('pathlib.Path.exists', return_value=True)
    def test_analyze_structure_with_bullets(self, mock_exists):
        converter = PDFConverter("test.pdf")

        blocks = [
            ("• Led team of developers", {"font_size": 11.0, "page": 0}),
            ("• Implemented new features", {"font_size": 11.0, "page": 0}),
            ("Regular text", {"font_size": 11.0, "page": 0}),
        ]

        structured = converter.analyze_structure(blocks)

        # First structured item should be a list
        assert structured[0]["type"] == "list"
        assert len(structured[0]["content"]) == 2
        assert "Led team" in structured[0]["content"][0]

    @patch('pathlib.Path.exists', return_value=True)
    def test_analyze_empty_blocks(self, mock_exists):
        converter = PDFConverter("test.pdf")

        structured = converter.analyze_structure([])

        assert structured == []


class TestLatexConversion:
    """Test LaTeX conversion."""

    @patch('resume_to_latex.pdf_converter.fitz.open')
    @patch('pathlib.Path.exists', return_value=True)
    def test_convert_to_latex_structure(self, mock_exists, mock_fitz_open):
        # Mock PDF document
        mock_doc = MagicMock()
        mock_page = MagicMock()

        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "type": 0,
                    "lines": [{"spans": [{"text": "John Smith", "size": 16.0}]}]
                },
                {
                    "type": 0,
                    "lines": [{"spans": [{"text": "EXPERIENCE", "size": 14.0}]}]
                }
            ]
        }

        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.close = Mock()
        mock_fitz_open.return_value = mock_doc

        converter = PDFConverter("test.pdf")
        latex = converter.convert_to_latex()

        # Check document structure
        assert "\\documentclass" in latex
        assert "\\begin{document}" in latex
        assert "\\end{document}" in latex

        # Check content
        assert "John Smith" in latex
        assert "EXPERIENCE" in latex

    @patch('resume_to_latex.pdf_converter.fitz.open')
    @patch('pathlib.Path.exists', return_value=True)
    def test_save_latex(self, mock_exists, mock_fitz_open, tmp_path):
        # Mock PDF document
        mock_doc = MagicMock()
        mock_page = MagicMock()

        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "type": 0,
                    "lines": [{"spans": [{"text": "Test Content", "size": 12.0}]}]
                }
            ]
        }

        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.close = Mock()
        mock_fitz_open.return_value = mock_doc

        converter = PDFConverter("test.pdf")
        output_path = tmp_path / "output.tex"

        converter.save_latex(str(output_path))

        assert output_path.exists()
        content = output_path.read_text()
        assert "\\documentclass" in content
        assert "Test Content" in content
