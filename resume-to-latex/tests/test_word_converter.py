"""Tests for Word document converter."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from resume_to_latex.word_converter import WordConverter


class TestWordConverterInit:
    """Test Word converter initialization."""

    def test_init_with_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            WordConverter("/path/to/nonexistent.docx")


class TestParagraphExtraction:
    """Test paragraph extraction from Word documents."""

    @patch('resume_to_latex.word_converter.Document')
    @patch('pathlib.Path.exists', return_value=True)
    def test_extract_paragraphs(self, mock_exists, mock_document_class):
        # Mock Word document
        mock_doc = MagicMock()

        # Create mock paragraphs
        mock_para1 = MagicMock()
        mock_para1.text = "John Smith"
        mock_para1.style.name = "Title"
        mock_para1.runs = []

        mock_para2 = MagicMock()
        mock_para2.text = "Software Engineer"
        mock_para2.style.name = "Normal"
        mock_para2.runs = []

        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_document_class.return_value = mock_doc

        converter = WordConverter("test.docx")
        paragraphs = converter.extract_paragraphs()

        assert len(paragraphs) == 2
        assert paragraphs[0]["text"] == "John Smith"
        assert paragraphs[1]["text"] == "Software Engineer"

    @patch('resume_to_latex.word_converter.Document')
    @patch('pathlib.Path.exists', return_value=True)
    def test_extract_paragraphs_with_font_info(self, mock_exists, mock_document_class):
        mock_doc = MagicMock()

        mock_para = MagicMock()
        mock_para.text = "Important Text"
        mock_para.style.name = "Normal"

        # Mock a run with font size
        mock_run = MagicMock()
        mock_run.font.size.pt = 14.0
        mock_run.bold = True

        mock_para.runs = [mock_run]
        mock_doc.paragraphs = [mock_para]
        mock_document_class.return_value = mock_doc

        converter = WordConverter("test.docx")
        paragraphs = converter.extract_paragraphs()

        assert paragraphs[0]["font_size"] == 14.0
        assert paragraphs[0]["is_bold"] is True

    @patch('resume_to_latex.word_converter.Document')
    @patch('pathlib.Path.exists', return_value=True)
    def test_extract_paragraphs_skips_empty(self, mock_exists, mock_document_class):
        mock_doc = MagicMock()

        mock_para1 = MagicMock()
        mock_para1.text = "   "  # Whitespace only
        mock_para1.style.name = "Normal"
        mock_para1.runs = []

        mock_para2 = MagicMock()
        mock_para2.text = "Valid Text"
        mock_para2.style.name = "Normal"
        mock_para2.runs = []

        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_document_class.return_value = mock_doc

        converter = WordConverter("test.docx")
        paragraphs = converter.extract_paragraphs()

        # Should only have the valid paragraph
        assert len(paragraphs) == 1
        assert paragraphs[0]["text"] == "Valid Text"


class TestStructureAnalysis:
    """Test document structure analysis for Word documents."""

    @patch('pathlib.Path.exists', return_value=True)
    def test_analyze_structure_with_name(self, mock_exists):
        converter = WordConverter("test.docx")

        paragraphs = [
            {
                "text": "John Smith",
                "style": "Title",
                "is_heading": True,
                "is_bold": True,
                "font_size": 16.0
            },
            {
                "text": "john@email.com",
                "style": "Normal",
                "is_heading": False,
                "is_bold": False,
                "font_size": 11.0
            }
        ]

        structured = converter.analyze_structure(paragraphs)

        assert structured[0]["type"] == "name"
        assert structured[0]["content"] == "John Smith"

    @patch('pathlib.Path.exists', return_value=True)
    def test_analyze_structure_with_headings(self, mock_exists):
        converter = WordConverter("test.docx")

        paragraphs = [
            {
                "text": "EXPERIENCE",
                "style": "Heading 1",
                "is_heading": True,
                "is_bold": True,
                "font_size": 14.0
            },
            {
                "text": "Description",
                "style": "Normal",
                "is_heading": False,
                "is_bold": False,
                "font_size": 11.0
            }
        ]

        structured = converter.analyze_structure(paragraphs)

        assert structured[0]["type"] == "section"
        assert structured[0]["content"] == "EXPERIENCE"

    @patch('pathlib.Path.exists', return_value=True)
    def test_analyze_structure_with_bullets(self, mock_exists):
        converter = WordConverter("test.docx")

        paragraphs = [
            {
                "text": "• Led development team",
                "style": "Normal",
                "is_heading": False,
                "is_bold": False,
                "font_size": 11.0
            },
            {
                "text": "• Implemented features",
                "style": "Normal",
                "is_heading": False,
                "is_bold": False,
                "font_size": 11.0
            },
            {
                "text": "Regular text",
                "style": "Normal",
                "is_heading": False,
                "is_bold": False,
                "font_size": 11.0
            }
        ]

        structured = converter.analyze_structure(paragraphs)

        # First item should be a list
        assert structured[0]["type"] == "list"
        assert len(structured[0]["content"]) == 2

    @patch('pathlib.Path.exists', return_value=True)
    def test_analyze_structure_with_bold_short_text(self, mock_exists):
        converter = WordConverter("test.docx")

        paragraphs = [
            {
                "text": "Skills",
                "style": "Normal",
                "is_heading": False,
                "is_bold": True,
                "font_size": 11.0
            }
        ]

        structured = converter.analyze_structure(paragraphs)

        # Bold short text should be treated as section
        assert structured[0]["type"] == "section"


class TestLatexConversion:
    """Test LaTeX conversion from Word documents."""

    @patch('resume_to_latex.word_converter.Document')
    @patch('pathlib.Path.exists', return_value=True)
    def test_convert_to_latex_structure(self, mock_exists, mock_document_class):
        mock_doc = MagicMock()

        # Create mock paragraphs
        mock_para1 = MagicMock()
        mock_para1.text = "John Smith"
        mock_para1.style.name = "Title"
        mock_para1.runs = []

        mock_para2 = MagicMock()
        mock_para2.text = "EDUCATION"
        mock_para2.style.name = "Heading 1"
        mock_para2.runs = []

        mock_para3 = MagicMock()
        mock_para3.text = "Bachelor's Degree"
        mock_para3.style.name = "Normal"
        mock_para3.runs = []

        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]
        mock_document_class.return_value = mock_doc

        converter = WordConverter("test.docx")
        latex = converter.convert_to_latex()

        # Check document structure
        assert "\\documentclass" in latex
        assert "\\begin{document}" in latex
        assert "\\end{document}" in latex

        # Check content
        assert "John Smith" in latex
        assert "EDUCATION" in latex
        assert "Bachelor" in latex

    @patch('resume_to_latex.word_converter.Document')
    @patch('pathlib.Path.exists', return_value=True)
    def test_save_latex(self, mock_exists, mock_document_class, tmp_path):
        mock_doc = MagicMock()

        mock_para = MagicMock()
        mock_para.text = "Test Content"
        mock_para.style.name = "Normal"
        mock_para.runs = []

        mock_doc.paragraphs = [mock_para]
        mock_document_class.return_value = mock_doc

        converter = WordConverter("test.docx")
        output_path = tmp_path / "output.tex"

        converter.save_latex(str(output_path))

        assert output_path.exists()
        content = output_path.read_text()
        assert "\\documentclass" in content
        assert "Test Content" in content
