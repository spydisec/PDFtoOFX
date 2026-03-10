"""ANZ Plus PDF parser"""
import re
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from app.models import Transaction, Statement, TransactionType, AccountType
from app.services.pdf_extractor import extract_transactions_from_pdf, extract_header_info
from app.logging_config import get_logger

logger = get_logger(__name__)


def smart_truncate(description: str, max_len: int = 32) -> str:
    """
    Intelligently truncate description to preserve merchant name.
    Removes common prefixes before truncating.
    
    Args:
        description: Full transaction description
        max_len: Maximum length (default 32 for OFX NAME field)
        
    Returns:
        Truncated description with merchant name preserved
    """
    # Common prefixes to remove (card-related only)
    # Transfer/payment prefixes are kept — they ARE the payee identity
    prefixes = [
        'VISA DEBIT PURCHASE CARD 1633 ',
        'VISA DEBIT PURCHASE CARD ',
        'EFTPOS ',
    ]
    
    clean = description
    for prefix in prefixes:
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
            break
    
    # Truncate if still too long
    if len(clean) > max_len:
        return clean[:max_len]
    
    return clean


class AnzPlusParser:
    """Parser for ANZ Plus PDF transaction lists"""
    
    # Transaction line pattern (for text-based fallback)
    TRANSACTION_PATTERN = r'^(\d{1,2})\s+([A-Z][a-z]{2})\s+(.+?)\s+\$?([\d,]+\.\d{2})(?:\s+\$?([\d,]+\.\d{2}))?$'
    
    def __init__(self, year: int = None):
        """
        Initialize parser with optional year.
        
        Args:
            year: Year for the statement (default: extracted from PDF or current year)
        """
        self.year = year or datetime.now().year
    
    def parse_pdf(self, pdf_path: Path) -> Statement:
        """Parse an ANZ Plus PDF file using column-aware extraction.

        Uses word positions to correctly distinguish Credit vs Debit columns.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            Statement object with transactions.
        """
        logger.info(f"Parsing PDF with column-aware extraction: {pdf_path}")

        # Extract header info (BSB, account, balances, year)
        info = extract_header_info(pdf_path)
        if info["year"]:
            self.year = info["year"]

        opening_balance = Decimal(info["opening_balance"]) if info["opening_balance"] else None
        closing_balance = Decimal(info["closing_balance"]) if info["closing_balance"] else None

        # Extract structured transaction rows
        raw_rows = extract_transactions_from_pdf(pdf_path)
        transactions: List[Transaction] = []

        for row in raw_rows:
            # Parse date
            try:
                txn_date = datetime.strptime(
                    f"{row['date_str']} {self.year}", "%d %b %Y"
                ).date()
            except ValueError:
                continue

            description = row["description"]
            balance = Decimal(row["balance"]) if row["balance"] else None

            # Credit/Debit is determined by which PDF column the amount was in
            if row["credit"]:
                amount = Decimal(row["credit"])
                txn_type = TransactionType.CREDIT
            elif row["debit"]:
                amount = Decimal(row["debit"])
                txn_type = TransactionType.DEBIT
            else:
                continue

            transactions.append(Transaction(
                date=txn_date,
                description=description,
                amount=amount,
                transaction_type=txn_type,
                balance=balance,
                name=smart_truncate(description, 32),
                memo=description,
            ))

        logger.info(f"Found {len(transactions)} transactions")

        # Date range
        if transactions:
            dates = [t.date for t in transactions]
            date_start, date_end = min(dates), max(dates)
        else:
            date_start = date_end = date.today()

        return Statement(
            account_name="ANZ Plus",
            account_number=info["account_number"],
            bsb=info["bsb"],
            account_type=AccountType.CHECKING,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            date_start=date_start,
            date_end=date_end,
            transactions=transactions,
        )

    def parse(self, text: str) -> Statement:
        """Parse ANZ Plus PDF text into Statement object (text-based fallback).
        
        Args:
            text: Extracted PDF text
            
        Returns:
            Statement object with transactions
        """
        logger.info("Starting ANZ Plus PDF parsing (text mode)")
        
        # Extract year from header
        year_match = re.search(r'(\d{1,2})\s+(\w+)\s+(20\d{2})', text)
        if year_match:
            self.year = int(year_match.group(3))

        # Extract opening/closing balances
        bal_match = re.search(
            r'(\d{3}\s*\d{3})\s+([\d\s]+?)\s+\$([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})',
            text,
        )
        if bal_match:
            bsb_raw, acct_raw, open_str, close_str = bal_match.groups()
            bsb = bsb_raw.replace(" ", "")[:3] + "-" + bsb_raw.replace(" ", "")[3:]
            account_number = acct_raw.replace(" ", "")
            opening_balance = Decimal(open_str.replace(",", ""))
            closing_balance = Decimal(close_str.replace(",", ""))
        else:
            bsb = None
            account_number = "ANZPLUS"
            opening_balance = None
            closing_balance = None
        
        # Parse transactions
        transactions = self._parse_transactions_from_text(text)
        logger.info(f"Found {len(transactions)} transactions")
        
        if transactions:
            dates = [t.date for t in transactions]
            date_start, date_end = min(dates), max(dates)
        else:
            date_start = date_end = date.today()
        
        return Statement(
            account_name="ANZ Plus",
            account_number=account_number,
            bsb=bsb,
            account_type=AccountType.CHECKING,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            date_start=date_start,
            date_end=date_end,
            transactions=transactions,
        )
    
    def _parse_transactions_from_text(self, text: str) -> List[Transaction]:
        """Parse transactions from plain text (fallback when PDF path unavailable)."""
        transactions = []
        lines = text.split('\n')
        next_balance = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            match = re.match(self.TRANSACTION_PATTERN, line)
            if match:
                day_str, month_abbr, description, amount_str, balance_str = match.groups()
                
                try:
                    txn_date = datetime.strptime(f"{day_str} {month_abbr} {self.year}", "%d %b %Y").date()
                except ValueError:
                    i += 1
                    continue
                
                description = description.strip()
                
                # Capture multi-line descriptions
                j = i + 1
                continuation_parts = []
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line.startswith('Effective Date'):
                        break
                    if re.match(self.TRANSACTION_PATTERN, next_line):
                        break
                    if not next_line or 'Page' in next_line or 'Australia and New Zealand' in next_line:
                        break
                    if next_line.startswith('Date') and 'Description' in next_line:
                        break
                    continuation_parts.append(next_line)
                    j += 1
                
                if continuation_parts:
                    full_description = ' '.join([description] + continuation_parts)
                    full_description = ' '.join(full_description.split())
                else:
                    full_description = description
                
                amount = Decimal(amount_str.replace(',', ''))
                balance = Decimal(balance_str.replace(',', '')) if balance_str else None
                
                transaction_type = self._determine_transaction_type(
                    full_description, balance, next_balance, amount
                )
                
                if balance is not None:
                    next_balance = balance
                
                transaction = Transaction(
                    date=txn_date,
                    description=full_description,
                    amount=amount,
                    transaction_type=transaction_type,
                    balance=balance,
                    name=smart_truncate(full_description, 32),
                    memo=full_description,
                )
                transactions.append(transaction)
            
            i += 1
        
        return transactions
    
    def _determine_transaction_type(
        self, 
        description: str, 
        current_balance: Optional[Decimal],
        balance_after: Optional[Decimal],
        amount: Decimal,
    ) -> TransactionType:
        """Determine if transaction is CREDIT or DEBIT (text-based fallback).
        
        Args:
            description: Transaction description
            current_balance: Balance at this transaction's date
            balance_after: Balance at a later date (from previous PDF line)
            amount: Transaction amount
            
        Returns:
            TransactionType.CREDIT or TransactionType.DEBIT
        """
        # Balance change is ground truth
        if current_balance is not None and balance_after is not None:
            delta = balance_after - current_balance
            if delta < 0:
                return TransactionType.DEBIT
            elif delta > 0:
                return TransactionType.CREDIT
        
        # Keyword fallback
        desc_upper = description.upper()
        
        for kw in ['PAYMENT FROM', 'TRANSFER FROM', 'ROUND UP FROM']:
            if kw in desc_upper:
                return TransactionType.CREDIT
        for kw in ['PAYMENT TO', 'TRANSFER TO', 'ROUND UP TO']:
            if kw in desc_upper:
                return TransactionType.DEBIT
        
        for kw in ['DEPOSIT', 'REFUND', 'SALARY', 'INTEREST CREDIT', 'INTEREST PAID', 'REVERSAL']:
            if kw in desc_upper:
                return TransactionType.CREDIT
        for kw in ['VISA DEBIT', 'EFTPOS', 'WITHDRAWAL', 'ATM', 'DIRECT DEBIT', 'FEE', 'CHARGE']:
            if kw in desc_upper:
                return TransactionType.DEBIT
        
        return TransactionType.DEBIT

