"""FITID (Financial Transaction ID) generator with collision-free guarantee"""
from datetime import date
from decimal import Decimal
from typing import Set


class FitidGenerator:
    """
    Generates unique FITIDs for OFX transactions.
    
    Strategy: Use date + sequential counter to guarantee uniqueness within statement.
    Format: ANZ_YYYYMMDD_NNNN
    Example: ANZ_20260121_0001, ANZ_20260121_0002
    
    This is deterministic and collision-free for transactions within the same statement.
    """
    
    def __init__(self, bank_prefix: str = "ANZ"):
        """
        Initialize FITID generator.
        
        Args:
            bank_prefix: Prefix for FITIDs (e.g., "ANZ", "CBA", "UP")
        """
        self.bank_prefix = bank_prefix
        self.used_fitids: Set[str] = set()
        self.date_counters: dict[date, int] = {}
    
    def generate(
        self,
        transaction_date: date,
        amount: Decimal,
        description: str,
        reference: str = None
    ) -> str:
        """
        Generate a unique FITID for a transaction.
        
        Priority 1: Use reference number if available (prefixed with bank code)
        Priority 2: Use date + sequential counter
        
        Args:
            transaction_date: Date of the transaction
            amount: Transaction amount
            description: Transaction description
            reference: Optional bank reference number
            
        Returns:
            Unique FITID string (max 32 chars for OFX compatibility)
        """
        # Priority 1: Use reference if provided
        if reference:
            fitid = f"{self.bank_prefix}_{reference}"
            if len(fitid) <= 32:
                self.used_fitids.add(fitid)
                return fitid
        
        # Priority 2: Date + sequential counter
        if transaction_date not in self.date_counters:
            self.date_counters[transaction_date] = 0
        
        # Generate FITID with counter
        while True:
            self.date_counters[transaction_date] += 1
            counter = self.date_counters[transaction_date]
            
            date_str = transaction_date.strftime("%Y%m%d")
            fitid = f"{self.bank_prefix}_{date_str}_{counter:04d}"
            
            # Check for collision (should never happen with sequential counter)
            if fitid not in self.used_fitids:
                self.used_fitids.add(fitid)
                return fitid
    
    def reset(self):
        """Reset the generator (for processing new statement)"""
        self.used_fitids.clear()
        self.date_counters.clear()
