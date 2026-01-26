"""Data models for PDF to OFX conversion"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TransactionType(str, Enum):
    """OFX transaction types"""
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class AccountType(str, Enum):
    """OFX account types"""
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"


class Transaction(BaseModel):
    """Represents a single bank transaction"""
    date: date
    description: str
    amount: Decimal
    transaction_type: TransactionType
    balance: Optional[Decimal] = None
    fitid: Optional[str] = None
    reference: Optional[str] = None
    
    # Store for OFX generation
    name: Optional[str] = None  # First 32 chars for OFX NAME field
    memo: Optional[str] = None  # Full description for OFX MEMO field
    
    @field_validator('amount')
    @classmethod
    def round_amount(cls, v: Decimal) -> Decimal:
        """Round amount to 2 decimal places"""
        return round(v, 2)
    
    def __post_init__(self):
        """Set name and memo from description if not provided"""
        if self.name is None:
            self.name = self.description[:32]
        if self.memo is None:
            self.memo = self.description


class Statement(BaseModel):
    """Represents a bank statement"""
    account_name: str
    account_number: str
    bsb: Optional[str] = None
    account_type: AccountType = AccountType.CHECKING
    opening_balance: Optional[Decimal] = None
    closing_balance: Optional[Decimal] = None
    date_start: date
    date_end: date
    transactions: list[Transaction] = Field(default_factory=list)
    
    @property
    def total_debits(self) -> Decimal:
        """Calculate total debit amount"""
        return sum(
            t.amount for t in self.transactions 
            if t.transaction_type == TransactionType.DEBIT
        )
    
    @property
    def total_credits(self) -> Decimal:
        """Calculate total credit amount"""
        return sum(
            t.amount for t in self.transactions 
            if t.transaction_type == TransactionType.CREDIT
        )


class BankConfig(BaseModel):
    """Bank-specific configuration"""
    name: str
    ofx_version: int = 220  # Default to OFX v2.20 (XML) for ANZ Plus/Up Bank
    bank_id: str = "633-123"  # ANZ Plus default
    currency: str = "AUD"
