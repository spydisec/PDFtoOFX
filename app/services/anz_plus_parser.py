"""ANZ Plus PDF parser"""
import re
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from dateutil import parser as date_parser

from app.models import Transaction, Statement, TransactionType, AccountType


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
    # Common prefixes to remove
    prefixes = [
        'VISA DEBIT PURCHASE CARD 1633 ',
        'VISA DEBIT PURCHASE CARD ',
        'EFTPOS ',
        'PAYMENT TO ',
        'TRANSFER TO ',
        'TRANSFER FROM ',
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
    
    # Account info patterns
    BSB_PATTERN = r'Branch Number \(BSB\)\s+Account Number\s+Balance as at.*?\n(\d+)\s+\$'
    ACCOUNT_PATTERN = r'Branch Number \(BSB\)\s+Account Number'
    BALANCE_PATTERN = r'Balance as at (\d+) ([A-Za-z]+) (\d{4})\s*\n\d+\s+\$?([\d,]+\.\d{2})'
    
    # Transaction line pattern
    # Format: "23 Jan ROUND UP TO 014111-169318495 #550672 $0.44 $232.16"
    # or: "22 Jan VISA DEBIT PURCHASE CARD 1633 MYKI $25.00 $233.45"
    TRANSACTION_PATTERN = r'^(\d{1,2})\s+([A-Z][a-z]{2})\s+(.+?)\s+\$?([\d,]+\.\d{2})(?:\s+\$?([\d,]+\.\d{2}))?$'
    
    # Effective date pattern (appears on next line sometimes)
    EFFECTIVE_DATE_PATTERN = r'Effective Date (\d{2})/(\d{2})/(\d{4})'
    
    def __init__(self, year: int = None):
        """
        Initialize parser with optional year.
        
        Args:
            year: Year for the statement (default: extracted from PDF or current year)
        """
        self.year = year or datetime.now().year
    
    def parse(self, text: str) -> Statement:
        """
        Parse ANZ Plus PDF text into Statement object.
        
        Args:
            text: Extracted PDF text
            
        Returns:
            Statement object with transactions
        """
        # Extract year from balance date if available
        balance_match = re.search(self.BALANCE_PATTERN, text)
        if balance_match:
            _, _, year_str, balance_str = balance_match.groups()
            self.year = int(year_str)
            closing_balance = Decimal(balance_str.replace(',', ''))
        else:
            closing_balance = None
        
        # Extract account number (simplified - ANZ Plus doesn't show full account in sample)
        account_number = "ANZPLUS"  # Placeholder
        
        # Parse transactions
        transactions = self._parse_transactions(text)
        
        # Determine date range from transactions
        if transactions:
            dates = [t.date for t in transactions]
            date_start = min(dates)
            date_end = max(dates)
        else:
            date_start = date_end = date.today()
        
        # Opening balance is the balance of the earliest transaction
        opening_balance = None
        if transactions:
            # Sort by date
            sorted_txns = sorted(transactions, key=lambda t: t.date)
            # Find first transaction with a balance
            for txn in sorted_txns:
                if txn.balance is not None:
                    # Calculate opening balance
                    if txn.transaction_type == TransactionType.DEBIT:
                        opening_balance = txn.balance + txn.amount
                    else:
                        opening_balance = txn.balance - txn.amount
                    break
        
        return Statement(
            account_name="ANZ Plus",
            account_number=account_number,
            bsb=None,  # Will extract from PDF if available
            account_type=AccountType.CHECKING,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            date_start=date_start,
            date_end=date_end,
            transactions=transactions
        )
    
    def _parse_transactions(self, text: str) -> List[Transaction]:
        """Parse all transactions from statement text with multi-line support"""
        transactions = []
        lines = text.split('\n')
        next_balance = None  # Track next transaction's balance (statements go newest->oldest)
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Try to match transaction line
            match = re.match(self.TRANSACTION_PATTERN, line)
            if match:
                day_str, month_abbr, description, amount_str, balance_str = match.groups()
                
                # Parse date
                try:
                    txn_date = datetime.strptime(f"{day_str} {month_abbr} {self.year}", "%d %b %Y").date()
                except ValueError:
                    i += 1
                    continue
                
                # Clean up description
                description = description.strip()
                
                # Skip "ROUND UP" transactions (micro-savings, not real spending)
                if description.startswith("ROUND UP TO"):
                    i += 1
                    continue
                
                # Capture multi-line descriptions
                # Look ahead for continuation lines (merchant details, location, reference)
                j = i + 1
                continuation_parts = []
                while j < len(lines):
                    next_line = lines[j].strip()
                    
                    # Stop at "Effective Date" line
                    if next_line.startswith('Effective Date'):
                        break
                    
                    # Stop if we hit another transaction
                    if re.match(self.TRANSACTION_PATTERN, next_line):
                        break
                    
                    # Stop if empty line or page footer
                    if not next_line or 'Page' in next_line or 'Australia and New Zealand' in next_line:
                        break
                    
                    # Stop if we hit table headers
                    if next_line.startswith('Date') and 'Description' in next_line:
                        break
                    
                    # This is a continuation line
                    continuation_parts.append(next_line)
                    j += 1
                
                # Concatenate multi-line description
                if continuation_parts:
                    # Join with space, clean up extra whitespace
                    full_description = ' '.join([description] + continuation_parts)
                    full_description = ' '.join(full_description.split())  # Normalize whitespace
                else:
                    full_description = description
                
                # Parse amounts
                amount = Decimal(amount_str.replace(',', ''))
                balance = Decimal(balance_str.replace(',', '')) if balance_str else None
                
                # Determine transaction type with improved logic
                # PDF lists newest→oldest, so we track balance_after_this_txn (chronologically)
                transaction_type = self._determine_transaction_type(
                    full_description, 
                    balance,  # Balance at this transaction date
                    next_balance,  # Balance at later date (chronologically) - from previous PDF line
                    amount
                )
                
                # Store current balance for next iteration
                # (next PDF line is chronologically earlier)
                if balance is not None:
                    next_balance = balance
                
                # Create transaction with smart truncation
                transaction = Transaction(
                    date=txn_date,
                    description=full_description,
                    amount=amount,
                    transaction_type=transaction_type,
                    balance=balance,
                    name=smart_truncate(full_description, 32),
                    memo=full_description
                )
                transactions.append(transaction)
            
            i += 1
        
        return transactions
    
    def _determine_transaction_type(
        self, 
        description: str, 
        current_balance: Optional[Decimal],
        balance_after: Optional[Decimal],
        amount: Decimal
    ) -> TransactionType:
        """
        Determine if transaction is CREDIT or DEBIT.
        
        Priority:
        1. Balance change calculation (most reliable)
        2. Keyword detection in description
        3. Default to DEBIT
        
        Args:
            description: Transaction description
            current_balance: Balance at this transaction's date
            balance_after: Balance at a later date (chronologically AFTER this transaction)
            amount: Transaction amount
            
        Returns:
            TransactionType.CREDIT or TransactionType.DEBIT
        """
        # Method 1: Calculate from balance changes (most reliable)
        # PDF shows newest→oldest, so balance_after is from a chronologically LATER date
        # Example: Current txn on Jan 20 has balance $258.45
        #          Later txn on Jan 22 has balance $233.45
        #          Change: $233.45 - $258.45 = -$25.00 (decreased = spent money = DEBIT)
        if current_balance is not None and balance_after is not None:
            balance_change = balance_after - current_balance
            # If balance decreased over time (negative change), money went out = DEBIT
            # If balance increased over time (positive change), money came in = CREDIT
            if balance_change < 0:
                return TransactionType.DEBIT
            elif balance_change > 0:
                return TransactionType.CREDIT
            # If balance_change == 0, fall through to keyword detection
        
        # Method 2: Keyword detection
        desc_upper = description.upper()
        
        # Credit keywords (money coming in)
        credit_keywords = [
            'PAYMENT FROM',
            'DEPOSIT',
            'TRANSFER FROM',
            'REFUND',
            'SALARY',
            'INTEREST CREDIT',
            'INTEREST PAID',
            'REVERSAL',
        ]
        
        # Debit keywords (money going out)
        debit_keywords = [
            'PAYMENT TO',
            'TRANSFER TO',
            'VISA DEBIT',
            'EFTPOS',
            'WITHDRAWAL',
            'ATM',
            'DIRECT DEBIT',
            'FEE',
            'CHARGE',
        ]
        
        # Check credit keywords first
        for keyword in credit_keywords:
            if keyword in desc_upper:
                return TransactionType.CREDIT
        
        # Check debit keywords
        for keyword in debit_keywords:
            if keyword in desc_upper:
                return TransactionType.DEBIT
        
        # Default to DEBIT (conservative approach)
        return TransactionType.DEBIT

