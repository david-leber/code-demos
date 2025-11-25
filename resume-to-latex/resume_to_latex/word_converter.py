"""Word document to LaTeX converter."""

from docx import Document
from docx.text.paragraph import Paragraph
from pathlib import Path
from typing import List
from .latex_formatter import LaTeXFormatter


class WordConverter:
    """Convert Word document resumes to LaTeX format."""

    def __init__(self, docx_path: str):
        """Initialize Word converter with path to DOCX file."""
        self.docx_path = Path(docx_path)
        if not self.docx_path.exists():
            raise FileNotFoundError(f"Word document not found: {docx_path}")

        self.formatter = LaTeXFormatter()
        self.doc = None

    def extract_paragraphs(self) -> List[dict]:
        """Extract paragraphs from Word document with formatting info."""
        self.doc = Document(self.docx_path)
        paragraphs = []

        for para in self.doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # Get paragraph style and formatting
            style_name = para.style.name if para.style else "Normal"
            is_heading = "Heading" in style_name or style_name.startswith("Title")

            # Check font size if available
            font_size = None
            if para.runs:
                for run in para.runs:
                    if run.font.size:
                        font_size = run.font.size.pt
                        break

            # Check if bold
            is_bold = False
            if para.runs:
                is_bold = any(run.bold for run in para.runs if run.bold is not None)

            paragraphs.append({
                "text": text,
                "style": style_name,
                "is_heading": is_heading,
                "is_bold": is_bold,
                "font_size": font_size,
            })

        return paragraphs

    def analyze_structure(self, paragraphs: List[dict]) -> List[dict]:
        """Analyze paragraphs to determine document structure."""
        if not paragraphs:
            return []

        structured = []
        current_list_items = []

        for i, para in enumerate(paragraphs):
            text = para["text"]

            # Determine block type
            if i == 0 and self.formatter.is_likely_name(text):
                block_type = "name"
            elif self.formatter.is_likely_contact_info(text):
                block_type = "contact"
            elif para["is_heading"] or para["is_bold"] and len(text.split()) <= 3:
                block_type = "section"
            elif self.formatter.detect_section_heading(text):
                block_type = "section"
            elif self.formatter.detect_bullet_point(text):
                block_type = "bullet"
            else:
                block_type = "text"

            # Handle list accumulation
            if block_type == "bullet":
                current_list_items.append(text)
            else:
                # Flush accumulated list items
                if current_list_items:
                    structured.append({
                        "type": "list",
                        "content": current_list_items.copy()
                    })
                    current_list_items = []

                structured.append({
                    "type": block_type,
                    "content": text
                })

        # Flush any remaining list items
        if current_list_items:
            structured.append({
                "type": "list",
                "content": current_list_items
            })

        return structured

    def convert_to_latex(self) -> str:
        """Convert Word document to LaTeX format."""
        # Extract and analyze text
        paragraphs = self.extract_paragraphs()
        structured = self.analyze_structure(paragraphs)

        # Generate LaTeX
        latex = self.formatter.generate_document_header()

        for block in structured:
            block_type = block["type"]
            content = block["content"]

            if block_type == "name":
                latex += self.formatter.format_name(content)
            elif block_type == "contact":
                latex += self.formatter.format_contact_info(content)
            elif block_type == "section":
                latex += self.formatter.format_section(content)
            elif block_type == "list":
                latex += self.formatter.format_list_items(content)
            elif block_type == "text":
                latex += self.formatter.format_paragraph(content)

        latex += self.formatter.generate_document_footer()

        return latex

    def save_latex(self, output_path: str) -> None:
        """Convert Word document to LaTeX and save to file."""
        latex_content = self.convert_to_latex()
        output_file = Path(output_path)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
