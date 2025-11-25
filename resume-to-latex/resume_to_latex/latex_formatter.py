"""LaTeX formatting utilities for resume conversion."""

import re
from typing import List


class LaTeXFormatter:
    """Utilities for formatting text as LaTeX."""

    @staticmethod
    def escape_latex(text: str) -> str:
        """Escape special LaTeX characters in text."""
        replacements = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
            '\\': r'\textbackslash{}',
        }

        for char, replacement in replacements.items():
            text = text.replace(char, replacement)

        return text

    @staticmethod
    def detect_section_heading(text: str) -> bool:
        """Detect if text is likely a section heading."""
        # Headings are typically short, all caps, or title case
        text = text.strip()
        if not text:
            return False

        # Common resume sections
        common_sections = [
            'education', 'experience', 'work experience', 'skills',
            'projects', 'certifications', 'awards', 'publications',
            'summary', 'objective', 'contact', 'references'
        ]

        return (
            text.isupper() or
            len(text.split()) <= 3 and text[0].isupper() or
            text.lower() in common_sections
        )

    @staticmethod
    def format_section(heading: str) -> str:
        """Format a section heading in LaTeX."""
        escaped = LaTeXFormatter.escape_latex(heading)
        return f"\\section{{{escaped}}}\n"

    @staticmethod
    def format_subsection(heading: str) -> str:
        """Format a subsection heading in LaTeX."""
        escaped = LaTeXFormatter.escape_latex(heading)
        return f"\\subsection{{{escaped}}}\n"

    @staticmethod
    def format_paragraph(text: str) -> str:
        """Format a paragraph in LaTeX."""
        escaped = LaTeXFormatter.escape_latex(text.strip())
        return f"{escaped}\n\n"

    @staticmethod
    def detect_bullet_point(text: str) -> bool:
        """Detect if text is a bullet point."""
        text = text.strip()
        return text.startswith(('•', '-', '*', '–', '—')) or re.match(r'^\d+\.', text)

    @staticmethod
    def format_list_items(items: List[str]) -> str:
        """Format a list of items in LaTeX."""
        if not items:
            return ""

        latex = "\\begin{itemize}\n"
        for item in items:
            # Remove leading bullet characters
            clean_item = re.sub(r'^[•\-\*–—]\s*', '', item.strip())
            clean_item = re.sub(r'^\d+\.\s*', '', clean_item)
            escaped = LaTeXFormatter.escape_latex(clean_item)
            latex += f"  \\item {escaped}\n"
        latex += "\\end{itemize}\n\n"

        return latex

    @staticmethod
    def generate_document_header(title: str = "Resume") -> str:
        """Generate LaTeX document header."""
        return r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=1in]{geometry}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{titlesec}

% Formatting
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.5em}
\titlespacing*{\section}{0pt}{1em}{0.5em}
\titlespacing*{\subsection}{0pt}{0.75em}{0.25em}

\begin{document}

"""

    @staticmethod
    def generate_document_footer() -> str:
        """Generate LaTeX document footer."""
        return "\\end{document}\n"

    @staticmethod
    def is_likely_name(text: str) -> bool:
        """Detect if text is likely a name (for title)."""
        text = text.strip()
        words = text.split()

        # Name is usually 2-4 words, title case, and relatively short
        if len(words) < 2 or len(words) > 4:
            return False

        # All words should start with capital letter
        if not all(word[0].isupper() for word in words if word):
            return False

        # Should be relatively short
        if len(text) > 50:
            return False

        return True

    @staticmethod
    def format_name(name: str) -> str:
        """Format a name as document title."""
        escaped = LaTeXFormatter.escape_latex(name.strip())
        return f"\\begin{{center}}\n  {{\\Large \\textbf{{{escaped}}}}}\n\\end{{center}}\n\n"

    @staticmethod
    def is_likely_contact_info(text: str) -> bool:
        """Detect if text contains contact information."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
        url_pattern = r'https?://|www\.'

        return bool(
            re.search(email_pattern, text) or
            re.search(phone_pattern, text) or
            re.search(url_pattern, text.lower())
        )

    @staticmethod
    def format_contact_info(text: str) -> str:
        """Format contact information."""
        escaped = LaTeXFormatter.escape_latex(text.strip())
        return f"\\begin{{center}}\n  {escaped}\n\\end{{center}}\n\n"
