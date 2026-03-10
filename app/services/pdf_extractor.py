"""PDF text extraction service"""
import re
from pathlib import Path
from typing import Optional

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


def extract_transactions_from_pdf(pdf_path: Path) -> list[dict]:
    """Extract structured transaction rows using word positions to distinguish Credit/Debit columns.

    ANZ Plus PDFs have separate Credit and Debit columns. Plain text extraction
    loses this distinction. This function uses word x-coordinates to determine
    which column each dollar amount belongs to.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        List of dicts with keys: date_str, description, credit, debit, balance.
        Dollar values are strings or None.
    """
    logger.info(f"Extracting structured transactions from: {pdf_path}")
    rows: list[dict] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                words = page.extract_words()
                if not words:
                    continue

                # Find column header positions on this page
                col_positions = _find_column_positions(words)
                if not col_positions:
                    logger.debug(f"Page {page_num}: no transaction table headers found")
                    continue

                # Group words by vertical position (same line)
                line_groups = _group_words_by_line(words, tolerance=3.0)

                # Parse each line for transaction data
                for line_top, line_words in sorted(line_groups.items()):
                    row = _parse_transaction_line(line_words, col_positions)
                    if row:
                        rows.append(row)

        logger.info(f"Extracted {len(rows)} structured transaction rows")
    except Exception as e:
        logger.error(f"Failed structured extraction: {str(e)}", exc_info=True)
        raise

    return rows


def extract_header_info(pdf_path: Path) -> dict:
    """Extract account header info (BSB, account number, balances) from PDF.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Dict with keys: bsb, account_number, opening_balance, closing_balance, year.
    """
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text() or ""

    info: dict = {
        "bsb": None,
        "account_number": "ANZPLUS",
        "opening_balance": None,
        "closing_balance": None,
        "year": None,
    }

    # Opening/Closing balance line: "014 111 169 318 022 $2,913.36 $9,713.36"
    m = re.search(
        r'(\d{3}\s*\d{3})\s+([\d\s]+?)\s+\$([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})',
        text,
    )
    if m:
        bsb_raw, acct_raw, open_bal, close_bal = m.groups()
        info["bsb"] = bsb_raw.replace(" ", "")[:3] + "-" + bsb_raw.replace(" ", "")[3:]
        info["account_number"] = acct_raw.replace(" ", "")
        info["opening_balance"] = open_bal.replace(",", "")
        info["closing_balance"] = close_bal.replace(",", "")

    # Year from "Commencing DD Month YYYY" or generated date
    year_match = re.search(r'(\d{1,2})\s+(\w+)\s+(20\d{2})', text)
    if year_match:
        info["year"] = int(year_match.group(3))

    return info


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


# --- Private helpers ---


def _find_column_positions(words: list[dict]) -> Optional[dict]:
    """Find x-positions of Credit, Debit, Balance column headers.

    Returns:
        Dict with 'credit_x', 'debit_x', 'balance_x' midpoints, or None.
    """
    headers: dict[str, float] = {}
    for w in words:
        text = w["text"].strip()
        if text in ("Credit", "Debit", "Balance"):
            mid = (w["x0"] + w["x1"]) / 2
            # Use the rightmost occurrence (transaction table, not account summary)
            if text not in headers or mid > headers.get(text, 0):
                # Only take headers in the right half of the page (transaction table)
                if w["x0"] > 350:
                    headers[text] = mid

    if "Credit" in headers and "Debit" in headers and "Balance" in headers:
        return {
            "credit_x": headers["Credit"],
            "debit_x": headers["Debit"],
            "balance_x": headers["Balance"],
        }
    return None


def _group_words_by_line(words: list[dict], tolerance: float = 3.0) -> dict[float, list[dict]]:
    """Group words into lines based on vertical position."""
    lines: dict[float, list[dict]] = {}
    for w in words:
        top = w["top"]
        # Find existing line within tolerance
        matched_top = None
        for existing_top in lines:
            if abs(existing_top - top) <= tolerance:
                matched_top = existing_top
                break
        if matched_top is not None:
            lines[matched_top].append(w)
        else:
            lines[top] = [w]
    return lines


def _parse_transaction_line(
    line_words: list[dict], col_positions: dict
) -> Optional[dict]:
    """Parse a single line of words into a transaction row.

    Returns:
        Dict with date_str, description, credit, debit, balance — or None if not a transaction.
    """
    # Sort words left to right
    line_words = sorted(line_words, key=lambda w: w["x0"])

    # First word(s) must be a date: "09" "Mar" pattern
    if len(line_words) < 3:
        return None

    day_word = line_words[0]["text"].strip()
    month_word = line_words[1]["text"].strip()

    # Validate date pattern
    if not re.match(r"^\d{1,2}$", day_word):
        return None
    if not re.match(r"^[A-Z][a-z]{2}$", month_word):
        return None

    # Classify dollar amounts by column position
    credit_x = col_positions["credit_x"]
    debit_x = col_positions["debit_x"]
    balance_x = col_positions["balance_x"]

    credit = None
    debit = None
    balance = None
    description_words: list[str] = []

    for w in line_words[2:]:  # Skip date words
        text = w["text"].strip()
        mid = (w["x0"] + w["x1"]) / 2

        if text.startswith("$"):
            # Classify by closest column header
            dist_credit = abs(mid - credit_x)
            dist_debit = abs(mid - debit_x)
            dist_balance = abs(mid - balance_x)
            min_dist = min(dist_credit, dist_debit, dist_balance)

            amount = text.lstrip("$").replace(",", "")
            if min_dist == dist_balance:
                balance = amount
            elif min_dist == dist_credit:
                credit = amount
            else:
                debit = amount
        else:
            description_words.append(text)

    description = " ".join(description_words).strip()
    if not description:
        return None

    return {
        "date_str": f"{day_word} {month_word}",
        "description": description,
        "credit": credit,
        "debit": debit,
        "balance": balance,
    }
