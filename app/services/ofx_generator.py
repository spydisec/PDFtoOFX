"""OFX file generator using ofxtools library"""
from datetime import datetime
from decimal import Decimal
from typing import List

from ofxtools.models import (
    OFX, SIGNONMSGSRSV1, SONRS, STATUS, FI,
    BANKMSGSRSV1, STMTTRNRS, STMTRS,
    BANKACCTFROM, BANKTRANLIST, STMTTRN,
    LEDGERBAL, AVAILBAL
)
from ofxtools.header import make_header
from ofxtools.utils import UTC

from app.models import Statement, Transaction, TransactionType, BankConfig
from app.services.fitid_generator import FitidGenerator


class OFXGenerator:
    """Generate OFX files from Statement objects using ofxtools"""
    
    def __init__(self, bank_config: BankConfig):
        """
        Initialize OFX generator.
        
        Args:
            bank_config: Bank-specific configuration
        """
        self.bank_config = bank_config
        self.fitid_generator = FitidGenerator(bank_prefix="ANZ")
    
    def generate(self, statement: Statement) -> bytes:
        """
        Generate OFX file from statement.
        
        Args:
            statement: Statement object with transactions
            
        Returns:
            OFX file content as bytes
        """
        # Generate FITIDs for all transactions
        self.fitid_generator.reset()
        transactions_with_fitid = []
        
        for txn in statement.transactions:
            if not txn.fitid:
                txn.fitid = self.fitid_generator.generate(
                    transaction_date=txn.date,
                    amount=txn.amount,
                    description=txn.description,
                    reference=txn.reference
                )
            transactions_with_fitid.append(txn)
        
        # Build OFX structure
        ofx = self._build_ofx(statement, transactions_with_fitid)
        
        # Generate header
        header = make_header(
            version=self.bank_config.ofx_version,
            oldfileuid="NONE",
            newfileuid="NONE"
        )
        
        # Serialize OFX
        from xml.etree.ElementTree import tostring
        body = tostring(
            ofx.to_etree(),
            encoding='unicode',
            method='html'  # Use 'html' to skip XML declaration (already in header)
        )
        
        # Combine header and body
        header_str = str(header)
        full_ofx = header_str + body
        
        return full_ofx.encode('utf-8')
    
    def _build_ofx(self, statement: Statement, transactions: List[Transaction]) -> OFX:
        """Build OFX object structure"""
        
        # Signon message
        sonrs = SONRS(
            status=STATUS(code=0, severity='INFO'),
            dtserver=datetime.now(UTC),
            language='ENG'
        )
        signonmsgsrsv1 = SIGNONMSGSRSV1(sonrs=sonrs)
        
        # Build transactions
        stmttrns = []
        for txn in transactions:
            # Convert amount to signed decimal (negative for debits in OFX)
            if txn.transaction_type == TransactionType.DEBIT:
                ofx_amount = -abs(txn.amount)
            else:
                ofx_amount = abs(txn.amount)
            
            # Convert date to datetime (midnight)
            dt = datetime.combine(txn.date, datetime.min.time()).replace(tzinfo=UTC)
            
            stmttrn = STMTTRN(
                trntype=txn.transaction_type.value,
                dtposted=dt,
                dtuser=dt,  # Same as dtposted for simplicity
                trnamt=ofx_amount,
                fitid=txn.fitid,
                name=txn.name or txn.description[:32],
                memo=txn.memo or txn.description
            )
            stmttrns.append(stmttrn)
        
        # Transaction list
        banktranlist = BANKTRANLIST(
            *stmttrns,
            dtstart=datetime.combine(statement.date_start, datetime.min.time()).replace(tzinfo=UTC),
            dtend=datetime.combine(statement.date_end, datetime.max.time()).replace(tzinfo=UTC)
        )
        
        # Account information
        bankacctfrom = BANKACCTFROM(
            bankid=statement.bsb or self.bank_config.bank_id,
            acctid=statement.account_number,
            accttype=statement.account_type.value
        )
        
        # Balances
        now = datetime.now(UTC)
        ledgerbal = LEDGERBAL(
            balamt=statement.closing_balance or Decimal('0.00'),
            dtasof=now
        )
        availbal = AVAILBAL(
            balamt=statement.closing_balance or Decimal('0.00'),
            dtasof=now
        )
        
        # Statement response
        stmtrs = STMTRS(
            curdef=self.bank_config.currency,
            bankacctfrom=bankacctfrom,
            banktranlist=banktranlist if stmttrns else None,
            ledgerbal=ledgerbal,
            availbal=availbal
        )
        
        # Wrap in transaction response
        stmttrnrs = STMTTRNRS(
            trnuid="1",  # Required by OFX spec
            status=STATUS(code=0, severity='INFO'),
            stmtrs=stmtrs
        )
        
        # Bank message set
        bankmsgsrsv1 = BANKMSGSRSV1(stmttrnrs)
        
        # Complete OFX
        return OFX(
            signonmsgsrsv1=signonmsgsrsv1,
            bankmsgsrsv1=bankmsgsrsv1
        )
