"""PDF text extraction service"""
from pathlib import Path
import pdfplumber
from app.logging_config import get_logger

logger = get_logger(__name__)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract all text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Concatenated text from all pages
    """
    logger.debug(f"Opening PDF file: {pdf_path}")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
            logger.info(f"PDF opened successfully: {page_count} pages")
            
            text_parts = []
            for i, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                    logger.debug(f"Extracted text from page {i}: {len(page_text)} characters")
                else:
                    logger.warning(f"No text extracted from page {i}")
            
            total_text = "\n\n".join(text_parts)
            logger.info(f"Total text extracted: {len(total_text)} characters from {len(text_parts)} pages")
            return total_text
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {pdf_path}: {str(e)}", exc_info=True)
        raise


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
