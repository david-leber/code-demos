"""PDF to LaTeX converter."""

import pymupdf as fitz
from pathlib import Path
from typing import List, Tuple
from .latex_formatter import LaTeXFormatter


class PDFConverter:
    """Convert PDF resumes to LaTeX format."""

    def __init__(self, pdf_path: str):
        """Initialize PDF converter with path to PDF file."""
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        self.formatter = LaTeXFormatter()
        self.doc = None

    def extract_text_blocks(self) -> List[Tuple[str, dict]]:
        """Extract text blocks from PDF with formatting information."""
        self.doc = fitz.open(self.pdf_path)
        blocks = []

        for page_num, page in enumerate(self.doc):
            # Get text blocks with position and formatting info
            text_blocks = page.get_text("dict")["blocks"]

            for block in text_blocks:
                if block.get("type") == 0:  # Text block
                    for line in block.get("lines", []):
                        text_parts = []
                        font_size = 0

                        for span in line.get("spans", []):
                            text_parts.append(span.get("text", ""))
                            font_size = max(font_size, span.get("size", 0))

                        text = "".join(text_parts).strip()
                        if text:
                            blocks.append((text, {"font_size": font_size, "page": page_num}))

        return blocks

    def analyze_structure(self, blocks: List[Tuple[str, dict]]) -> List[dict]:
        """Analyze text blocks to determine document structure."""
        if not blocks:
            return []

        # Calculate average font size
        font_sizes = [info["font_size"] for _, info in blocks]
        avg_font_size = sum(font_sizes) / len(font_sizes)

        structured = []
        current_list_items = []

        for i, (text, info) in enumerate(blocks):
            font_size = info["font_size"]
            is_large = font_size > avg_font_size * 1.1

            # Determine block type
            if i == 0 and self.formatter.is_likely_name(text):
                block_type = "name"
            elif self.formatter.is_likely_contact_info(text):
                block_type = "contact"
            elif is_large or self.formatter.detect_section_heading(text):
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
        """Convert PDF to LaTeX format."""
        try:
            # Extract and analyze text
            blocks = self.extract_text_blocks()
            structured = self.analyze_structure(blocks)

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

        finally:
            if self.doc:
                self.doc.close()

    def save_latex(self, output_path: str) -> None:
        """Convert PDF to LaTeX and save to file."""
        latex_content = self.convert_to_latex()
        output_file = Path(output_path)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
