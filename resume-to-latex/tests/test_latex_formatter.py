"""Tests for LaTeX formatter."""

from resume_to_latex.latex_formatter import LaTeXFormatter


class TestLatexEscaping:
    """Test LaTeX special character escaping."""

    def test_escape_ampersand(self):
        result = LaTeXFormatter.escape_latex("Research & Development")
        assert result == r"Research \& Development"

    def test_escape_percent(self):
        result = LaTeXFormatter.escape_latex("100% complete")
        assert result == r"100\% complete"

    def test_escape_dollar(self):
        result = LaTeXFormatter.escape_latex("Earned $50,000")
        assert result == r"Earned \$50,000"

    def test_escape_hash(self):
        result = LaTeXFormatter.escape_latex("Issue #123")
        assert result == r"Issue \#123"

    def test_escape_underscore(self):
        result = LaTeXFormatter.escape_latex("file_name.txt")
        assert result == r"file\_name.txt"

    def test_escape_braces(self):
        result = LaTeXFormatter.escape_latex("Use {brackets}")
        assert result == r"Use \{brackets\}"

    def test_escape_tilde(self):
        result = LaTeXFormatter.escape_latex("path~to~file")
        assert result == r"path\textasciitilde{}to\textasciitilde{}file"

    def test_escape_caret(self):
        result = LaTeXFormatter.escape_latex("x^2")
        assert result == r"x\textasciicircum{}2"

    def test_escape_backslash(self):
        result = LaTeXFormatter.escape_latex("C:\\Users\\Name")
        assert result == r"C:\textbackslash{}Users\textbackslash{}Name"

    def test_escape_multiple_special_chars(self):
        result = LaTeXFormatter.escape_latex("C&C++ #1 @ 100% ($50)")
        assert result == r"C\&C++ \#1 @ 100\% (\$50)"

    def test_escape_empty_string(self):
        result = LaTeXFormatter.escape_latex("")
        assert result == ""


class TestSectionDetection:
    """Test section heading detection."""

    def test_detect_all_caps_heading(self):
        assert LaTeXFormatter.detect_section_heading("EDUCATION")
        assert LaTeXFormatter.detect_section_heading("WORK EXPERIENCE")

    def test_detect_title_case_short_heading(self):
        assert LaTeXFormatter.detect_section_heading("Education")
        assert LaTeXFormatter.detect_section_heading("Skills")

    def test_detect_common_section_names(self):
        assert LaTeXFormatter.detect_section_heading("experience")
        assert LaTeXFormatter.detect_section_heading("Education")
        assert LaTeXFormatter.detect_section_heading("CERTIFICATIONS")

    def test_not_detect_long_text(self):
        assert not LaTeXFormatter.detect_section_heading("This is a long paragraph of text")

    def test_not_detect_empty_string(self):
        assert not LaTeXFormatter.detect_section_heading("")


class TestBulletDetection:
    """Test bullet point detection."""

    def test_detect_bullet_with_unicode(self):
        assert LaTeXFormatter.detect_bullet_point("• Managed team of 5")

    def test_detect_bullet_with_hyphen(self):
        assert LaTeXFormatter.detect_bullet_point("- Implemented feature")

    def test_detect_bullet_with_asterisk(self):
        assert LaTeXFormatter.detect_bullet_point("* Created dashboard")

    def test_detect_numbered_bullet(self):
        assert LaTeXFormatter.detect_bullet_point("1. First item")
        assert LaTeXFormatter.detect_bullet_point("12. Twelfth item")

    def test_not_detect_regular_text(self):
        assert not LaTeXFormatter.detect_bullet_point("Regular paragraph text")


class TestFormatting:
    """Test LaTeX formatting functions."""

    def test_format_section(self):
        result = LaTeXFormatter.format_section("Education")
        assert result == "\\section{Education}\n"

    def test_format_section_with_special_chars(self):
        result = LaTeXFormatter.format_section("Skills & Abilities")
        assert result == "\\section{Skills \\& Abilities}\n"

    def test_format_subsection(self):
        result = LaTeXFormatter.format_subsection("Bachelor's Degree")
        assert result == "\\subsection{Bachelor's Degree}\n"

    def test_format_paragraph(self):
        result = LaTeXFormatter.format_paragraph("This is a test paragraph.")
        assert result == "This is a test paragraph.\n\n"

    def test_format_paragraph_strips_whitespace(self):
        result = LaTeXFormatter.format_paragraph("  Text with spaces  ")
        assert result == "Text with spaces\n\n"

    def test_format_list_items(self):
        items = ["• First item", "• Second item", "• Third item"]
        result = LaTeXFormatter.format_list_items(items)
        assert "\\begin{itemize}" in result
        assert "\\end{itemize}" in result
        assert "\\item First item" in result
        assert "\\item Second item" in result
        assert "\\item Third item" in result

    def test_format_list_removes_bullets(self):
        items = ["- Item one", "* Item two", "• Item three"]
        result = LaTeXFormatter.format_list_items(items)
        assert "\\item Item one" in result
        assert "\\item Item two" in result
        assert "\\item Item three" in result

    def test_format_list_removes_numbers(self):
        items = ["1. First", "2. Second", "3. Third"]
        result = LaTeXFormatter.format_list_items(items)
        assert "\\item First" in result
        assert "\\item Second" in result

    def test_format_empty_list(self):
        result = LaTeXFormatter.format_list_items([])
        assert result == ""


class TestNameDetection:
    """Test name detection."""

    def test_detect_simple_name(self):
        assert LaTeXFormatter.is_likely_name("John Smith")
        assert LaTeXFormatter.is_likely_name("Mary Jane Watson")

    def test_detect_name_with_middle_initial(self):
        assert LaTeXFormatter.is_likely_name("John Q. Public")

    def test_not_detect_single_word(self):
        assert not LaTeXFormatter.is_likely_name("Education")

    def test_not_detect_long_text(self):
        assert not LaTeXFormatter.is_likely_name("This is a very long text that is not a name")

    def test_not_detect_lowercase(self):
        assert not LaTeXFormatter.is_likely_name("john smith")

    def test_not_detect_too_many_words(self):
        assert not LaTeXFormatter.is_likely_name("This Has Five Words Here")


class TestContactInfo:
    """Test contact information detection."""

    def test_detect_email(self):
        assert LaTeXFormatter.is_likely_contact_info("john.doe@example.com")
        assert LaTeXFormatter.is_likely_contact_info("Contact: email@domain.org")

    def test_detect_phone(self):
        assert LaTeXFormatter.is_likely_contact_info("123-456-7890")
        assert LaTeXFormatter.is_likely_contact_info("(555) 123-4567")
        assert LaTeXFormatter.is_likely_contact_info("555.123.4567")

    def test_detect_url(self):
        assert LaTeXFormatter.is_likely_contact_info("https://linkedin.com/in/johndoe")
        assert LaTeXFormatter.is_likely_contact_info("www.github.com/user")

    def test_not_detect_regular_text(self):
        assert not LaTeXFormatter.is_likely_contact_info("Regular text without contact info")


class TestDocumentStructure:
    """Test document header and footer generation."""

    def test_generate_header(self):
        result = LaTeXFormatter.generate_document_header()
        assert "\\documentclass" in result
        assert "\\begin{document}" in result
        assert "\\usepackage" in result

    def test_generate_footer(self):
        result = LaTeXFormatter.generate_document_footer()
        assert result == "\\end{document}\n"

    def test_format_name_as_title(self):
        result = LaTeXFormatter.format_name("John Smith")
        assert "\\Large" in result or "\\textbf" in result
        assert "John Smith" in result
        assert "\\begin{center}" in result

    def test_format_contact_centered(self):
        result = LaTeXFormatter.format_contact_info("john@example.com | 555-1234")
        assert "\\begin{center}" in result
        assert "\\end{center}" in result
