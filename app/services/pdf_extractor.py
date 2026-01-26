"""PDF text extraction service"""
from pathlib import Path
import pdfplumber


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract all text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Concatenated text from all pages
    """
    with pdfplumber.open(pdf_path) as pdf:
        text_parts = []
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        return "\n\n".join(text_parts)


def extract_first_page(pdf_path: Path) -> str:
    """
    Extract text from first page only (useful for bank detection).
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Text from first page
    """
    with pdfplumber.open(pdf_path) as pdf:
        if pdf.pages:
            return pdf.pages[0].extract_text() or ""
        return ""
