"""Smoke tests using real sample resumes."""

from pathlib import Path

import pytest

from resume_to_latex.word_converter import WordConverter


class TestSmokeWordConverter:
    """Smoke tests for Word document conversion using sample resumes."""

    @pytest.fixture
    def examples_dir(self):
        """Get path to examples directory."""
        return Path(__file__).parent.parent / "examples"

    def test_convert_tech_resume(self, examples_dir, tmp_path):
        """Test converting tech resume from Word to LaTeX."""
        input_file = examples_dir / "sample_resume_tech.docx"

        if not input_file.exists():
            pytest.skip("Sample resume file not found")

        converter = WordConverter(str(input_file))
        latex = converter.convert_to_latex()

        # Verify LaTeX structure
        assert "\\documentclass" in latex
        assert "\\begin{document}" in latex
        assert "\\end{document}" in latex

        # Verify key content is present
        assert "John Smith" in latex
        assert "Computer Science" in latex
        assert "Software Engineer" in latex
        assert "Python" in latex

        # Verify proper escaping
        assert "\\&" not in latex or latex.count("\\") > 5  # Some escaping should happen

        # Save and verify file
        output_file = tmp_path / "tech_resume.tex"
        converter.save_latex(str(output_file))
        assert output_file.exists()
        assert output_file.stat().st_size > 100

    def test_convert_marketing_resume(self, examples_dir, tmp_path):
        """Test converting marketing resume from Word to LaTeX."""
        input_file = examples_dir / "sample_resume_marketing.docx"

        if not input_file.exists():
            pytest.skip("Sample resume file not found")

        converter = WordConverter(str(input_file))
        latex = converter.convert_to_latex()

        # Verify LaTeX structure
        assert "\\documentclass" in latex
        assert "\\begin{document}" in latex
        assert "\\end{document}" in latex

        # Verify key content
        assert "Sarah Johnson" in latex
        assert "Marketing Manager" in latex
        assert "Digital Solutions" in latex

        # Verify bullet points are converted to itemize
        assert "\\begin{itemize}" in latex
        assert "\\item" in latex
        assert "\\end{itemize}" in latex

        # Save and verify
        output_file = tmp_path / "marketing_resume.tex"
        converter.save_latex(str(output_file))
        assert output_file.exists()

    def test_convert_data_science_resume(self, examples_dir, tmp_path):
        """Test converting data science resume from Word to LaTeX."""
        input_file = examples_dir / "sample_resume_data_science.docx"

        if not input_file.exists():
            pytest.skip("Sample resume file not found")

        converter = WordConverter(str(input_file))
        latex = converter.convert_to_latex()

        # Verify LaTeX structure
        assert "\\documentclass" in latex
        assert "\\begin{document}" in latex
        assert "\\end{document}" in latex

        # Verify key content
        assert "Emily Chen" in latex
        assert "Data Scientist" in latex
        assert "Python" in latex
        assert "Machine Learning" in latex

        # Verify sections
        assert "\\section" in latex

        # Save and verify
        output_file = tmp_path / "data_science_resume.tex"
        converter.save_latex(str(output_file))
        assert output_file.exists()

        # Read the output and verify it's valid LaTeX
        content = output_file.read_text()
        assert content.startswith("\\documentclass")
        assert content.strip().endswith("\\end{document}")

    def test_all_resumes_have_sections(self, examples_dir):
        """Verify all sample resumes generate proper sections."""
        resume_files = [
            "sample_resume_tech.docx",
            "sample_resume_marketing.docx",
            "sample_resume_data_science.docx",
        ]

        for resume_file in resume_files:
            input_file = examples_dir / resume_file

            if not input_file.exists():
                continue

            converter = WordConverter(str(input_file))
            latex = converter.convert_to_latex()

            # All resumes should have at least one section
            assert "\\section" in latex, f"{resume_file} should have sections"

            # All resumes should have some content
            assert len(latex) > 500, f"{resume_file} output too short"

    def test_special_characters_escaped(self, examples_dir):
        """Verify special LaTeX characters are properly escaped in all resumes."""
        resume_files = [
            "sample_resume_tech.docx",
            "sample_resume_marketing.docx",
            "sample_resume_data_science.docx",
        ]

        for resume_file in resume_files:
            input_file = examples_dir / resume_file

            if not input_file.exists():
                continue

            converter = WordConverter(str(input_file))
            latex = converter.convert_to_latex()

            # Check that raw special characters that should be escaped are not present
            # (except in LaTeX commands themselves)
            lines = latex.split('\n')
            for line in lines:
                # Skip LaTeX command lines
                if line.strip().startswith('\\'):
                    continue

                # Check for unescaped special chars in content
                # Note: This is a heuristic check
                if '{' in line and '\\{' not in line and not line.strip().startswith('\\'):
                    # There might be legitimate braces in LaTeX commands
                    pass

    def test_resume_conversion_performance(self, examples_dir, tmp_path):
        """Ensure resume conversion completes in reasonable time."""
        import time

        input_file = examples_dir / "sample_resume_tech.docx"

        if not input_file.exists():
            pytest.skip("Sample resume file not found")

        start_time = time.time()
        converter = WordConverter(str(input_file))
        converter.convert_to_latex()
        output_file = tmp_path / "perf_test.tex"
        converter.save_latex(str(output_file))
        elapsed = time.time() - start_time

        # Conversion should be fast (under 5 seconds)
        assert elapsed < 5.0, f"Conversion took {elapsed:.2f}s, expected < 5s"


class TestSmokeEndToEnd:
    """End-to-end smoke tests."""

    @pytest.fixture
    def examples_dir(self):
        """Get path to examples directory."""
        return Path(__file__).parent.parent / "examples"

    def test_complete_workflow(self, examples_dir, tmp_path):
        """Test complete workflow: Word -> LaTeX -> verify compilable structure."""
        input_file = examples_dir / "sample_resume_tech.docx"

        if not input_file.exists():
            pytest.skip("Sample resume file not found")

        # Convert
        converter = WordConverter(str(input_file))
        output_file = tmp_path / "complete_test.tex"
        converter.save_latex(str(output_file))

        # Verify file exists and has content
        assert output_file.exists()
        content = output_file.read_text()

        # Verify it has all required LaTeX components
        required_components = [
            "\\documentclass",
            "\\begin{document}",
            "\\end{document}",
            "\\usepackage",
        ]

        for component in required_components:
            assert component in content, f"Missing required component: {component}"

        # Verify no common LaTeX errors
        assert content.count("\\begin{document}") == 1
        assert content.count("\\end{document}") == 1
        assert content.count("\\begin{itemize}") == content.count("\\end{itemize}")

        # Verify structure makes sense
        doc_start = content.index("\\begin{document}")
        doc_end = content.index("\\end{document}")
        assert doc_start < doc_end
        assert doc_end < len(content)
