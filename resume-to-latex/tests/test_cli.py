"""Tests for CLI interface."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from resume_to_latex.cli import detect_file_type, main


class TestFileTypeDetection:
    """Test file type detection."""

    def test_detect_pdf(self):
        result = detect_file_type(Path("resume.pdf"))
        assert result == "pdf"

    def test_detect_docx(self):
        result = detect_file_type(Path("resume.docx"))
        assert result == "word"

    def test_detect_doc(self):
        result = detect_file_type(Path("resume.doc"))
        assert result == "word"

    def test_detect_uppercase_extension(self):
        result = detect_file_type(Path("resume.PDF"))
        assert result == "pdf"

    def test_unsupported_extension(self):
        with pytest.raises(ValueError):
            detect_file_type(Path("resume.txt"))


class TestCLI:
    """Test CLI commands."""

    def setup_method(self):
        self.runner = CliRunner()

    def test_help_command(self):
        result = self.runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert "Convert resume from PDF or Word format to LaTeX" in result.output

    @patch('resume_to_latex.cli.PDFConverter')
    def test_convert_pdf(self, mock_pdf_converter_class, tmp_path):
        # Create a temporary PDF file
        input_file = tmp_path / "test.pdf"
        input_file.touch()

        tmp_path / "test.tex"

        # Mock the converter
        mock_converter = MagicMock()
        mock_pdf_converter_class.return_value = mock_converter

        result = self.runner.invoke(main, [str(input_file)])

        assert result.exit_code == 0
        assert "Converting test.pdf to LaTeX" in result.output
        assert "Successfully converted" in result.output
        mock_converter.save_latex.assert_called_once()

    @patch('resume_to_latex.cli.WordConverter')
    def test_convert_word(self, mock_word_converter_class, tmp_path):
        # Create a temporary Word file
        input_file = tmp_path / "test.docx"
        input_file.touch()

        tmp_path / "test.tex"

        # Mock the converter
        mock_converter = MagicMock()
        mock_word_converter_class.return_value = mock_converter

        result = self.runner.invoke(main, [str(input_file)])

        assert result.exit_code == 0
        assert "Converting test.docx to LaTeX" in result.output
        mock_converter.save_latex.assert_called_once()

    @patch('resume_to_latex.cli.PDFConverter')
    def test_convert_with_custom_output(self, mock_pdf_converter_class, tmp_path):
        # Create a temporary PDF file
        input_file = tmp_path / "test.pdf"
        input_file.touch()

        output_file = tmp_path / "custom_output.tex"

        # Mock the converter
        mock_converter = MagicMock()
        mock_pdf_converter_class.return_value = mock_converter

        result = self.runner.invoke(main, [str(input_file), '-o', str(output_file)])

        assert result.exit_code == 0
        mock_converter.save_latex.assert_called_once_with(str(output_file))

    @patch('resume_to_latex.cli.PDFConverter')
    def test_convert_with_explicit_type(self, mock_pdf_converter_class, tmp_path):
        # Create a temporary file with no extension
        input_file = tmp_path / "test.pdf"
        input_file.touch()

        # Mock the converter
        mock_converter = MagicMock()
        mock_pdf_converter_class.return_value = mock_converter

        result = self.runner.invoke(main, [str(input_file), '--type', 'pdf'])

        assert result.exit_code == 0
        mock_pdf_converter_class.assert_called_once()

    def test_convert_nonexistent_file(self):
        result = self.runner.invoke(main, ['/path/to/nonexistent.pdf'])

        # Click should catch this before our code runs
        assert result.exit_code != 0

    @patch('resume_to_latex.cli.PDFConverter')
    def test_convert_handles_conversion_error(self, mock_pdf_converter_class, tmp_path):
        # Create a temporary PDF file
        input_file = tmp_path / "test.pdf"
        input_file.touch()

        # Mock the converter to raise an error
        mock_converter = MagicMock()
        mock_converter.save_latex.side_effect = Exception("Conversion failed")
        mock_pdf_converter_class.return_value = mock_converter

        result = self.runner.invoke(main, [str(input_file)])

        assert result.exit_code != 0
        assert "Error during conversion" in result.output

    @patch('resume_to_latex.cli.PDFConverter')
    def test_output_includes_compile_instructions(self, mock_pdf_converter_class, tmp_path):
        # Create a temporary PDF file
        input_file = tmp_path / "test.pdf"
        input_file.touch()

        # Mock the converter
        mock_converter = MagicMock()
        mock_pdf_converter_class.return_value = mock_converter

        result = self.runner.invoke(main, [str(input_file)])

        assert result.exit_code == 0
        assert "pdflatex" in result.output
        assert "You can now edit the LaTeX file" in result.output
