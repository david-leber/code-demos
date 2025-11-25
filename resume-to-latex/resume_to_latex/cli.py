"""Command-line interface for resume-to-latex converter."""

import click
from pathlib import Path
from .pdf_converter import PDFConverter
from .word_converter import WordConverter


def detect_file_type(file_path: Path) -> str:
    """Detect file type from extension."""
    suffix = file_path.suffix.lower()
    if suffix == '.pdf':
        return 'pdf'
    elif suffix in ['.docx', '.doc']:
        return 'word'
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Supported types: .pdf, .docx, .doc")


@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option(
    '-o', '--output',
    type=click.Path(),
    help='Output LaTeX file path (default: input filename with .tex extension)'
)
@click.option(
    '-t', '--type',
    type=click.Choice(['pdf', 'word'], case_sensitive=False),
    help='Input file type (auto-detected if not specified)'
)
def main(input_file: str, output: str, type: str):
    """Convert resume from PDF or Word format to LaTeX.

    INPUT_FILE: Path to the resume file (.pdf, .docx, or .doc)

    Examples:

        \b
        # Convert PDF to LaTeX
        resume-to-latex resume.pdf

        \b
        # Convert Word document with custom output path
        resume-to-latex resume.docx -o my_resume.tex

        \b
        # Explicitly specify input type
        resume-to-latex resume.pdf --type pdf
    """
    input_path = Path(input_file)

    # Determine file type
    if type:
        file_type = type.lower()
    else:
        try:
            file_type = detect_file_type(input_path)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        output_path = input_path.with_suffix('.tex')

    # Convert based on file type
    try:
        click.echo(f"Converting {input_path.name} to LaTeX...")

        if file_type == 'pdf':
            converter = PDFConverter(str(input_path))
        elif file_type == 'word':
            converter = WordConverter(str(input_path))
        else:
            click.echo(f"Error: Unsupported file type '{file_type}'", err=True)
            raise click.Abort()

        converter.save_latex(str(output_path))
        click.echo(f"✓ Successfully converted to {output_path}")
        click.echo(f"\nYou can now edit the LaTeX file and compile it with:")
        click.echo(f"  pdflatex {output_path.name}")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error during conversion: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    main()
