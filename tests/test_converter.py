"""Tests for the ANZ Plus PDF to OFX converter"""
import pytest
from pathlib import Path
from decimal import Decimal
from datetime import date

from app.services.pdf_extractor import extract_text_from_pdf
from app.services.anz_plus_parser import AnzPlusParser
from app.services.fitid_generator import FitidGenerator
from app.services.ofx_generator import OFXGenerator
from app.models import BankConfig, TransactionType


class TestFitidGenerator:
    """Test FITID generation for collision-free guarantees"""
    
    def test_sequential_fitids_no_collision(self):
        """Test that sequential FITIDs never collide"""
        generator = FitidGenerator(bank_prefix="TEST")
        
        test_date = date(2026, 1, 15)
        fitids = set()
        
        # Generate 100 FITIDs for same date
        for i in range(100):
            fitid = generator.generate(
                transaction_date=test_date,
                amount=Decimal("10.00"),
                description=f"Transaction {i}"
            )
            assert fitid not in fitids, f"Collision detected: {fitid}"
            fitids.add(fitid)
            assert fitid.startswith("TEST_20260115_"), f"Unexpected format: {fitid}"
    
    def test_reference_number_priority(self):
        """Test that reference numbers are used when available"""
        generator = FitidGenerator(bank_prefix="ANZ")
        
        fitid = generator.generate(
            transaction_date=date(2026, 1, 15),
            amount=Decimal("10.00"),
            description="Test transaction",
            reference="REF123456"
        )
        
        assert fitid == "ANZ_REF123456"
    
    def test_different_dates_independent_counters(self):
        """Test that different dates have independent counters"""
        generator = FitidGenerator(bank_prefix="TEST")
        
        fitid1 = generator.generate(date(2026, 1, 15), Decimal("10"), "Test")
        fitid2 = generator.generate(date(2026, 1, 16), Decimal("10"), "Test")
        fitid3 = generator.generate(date(2026, 1, 15), Decimal("10"), "Test")
        
        assert fitid1 == "TEST_20260115_0001"
        assert fitid2 == "TEST_20260116_0001"
        assert fitid3 == "TEST_20260115_0002"


class TestAnzPlusParser:
    """Test ANZ Plus PDF parsing"""
    
    def test_parse_transaction_line(self):
        """Test parsing a single transaction line"""
        parser = AnzPlusParser(year=2026)
        text = """23 Jan VISA DEBIT PURCHASE CARD 1633 MYKI $25.00 $233.45
PAYMENTS MELBOURNE"""
        
        statement = parser.parse(text)
        assert len(statement.transactions) == 1
        
        txn = statement.transactions[0]
        assert txn.date == date(2026, 1, 23)
        assert txn.amount == Decimal("25.00")
        assert "MYKI" in txn.description
        assert txn.balance == Decimal("233.45")
    
    def test_skip_round_up_transactions(self):
        """Test that ROUND UP transactions are skipped"""
        parser = AnzPlusParser(year=2026)
        text = """23 Jan ROUND UP TO 014111-169318495 #550672 $0.44 $232.16
23 Jan VISA DEBIT PURCHASE CARD 1633 MYKI $25.00 $233.45"""
        
        statement = parser.parse(text)
        assert len(statement.transactions) == 1
        assert "MYKI" in statement.transactions[0].description


class TestEndToEnd:
    """End-to-end integration tests"""
    
    def test_full_conversion_produces_valid_ofx(self):
        """Test that the full conversion produces valid OFX output"""
        # This test requires the sample PDF file
        pdf_path = Path("examples/pdfs/sample_anz_plus.pdf")
        
        if not pdf_path.exists():
            pytest.skip("Sample PDF not available")
        
        # Extract and parse
        text = extract_text_from_pdf(pdf_path)
        parser = AnzPlusParser()
        statement = parser.parse(text)
        
        # Verify statement
        assert len(statement.transactions) > 0
        assert statement.closing_balance is not None
        
        # Generate OFX
        bank_config = BankConfig(
            name="ANZ Plus",
            ofx_version=220,
            bank_id="633-123",
            currency="AUD"
        )
        generator = OFXGenerator(bank_config)
        ofx_content = generator.generate(statement)
        
        # Verify OFX content
        ofx_str = ofx_content.decode('utf-8')
        assert '<?xml version="1.0"' in ofx_str
        assert 'OFXHEADER="200"' in ofx_str
        assert 'VERSION="220"' in ofx_str
        assert '<CURDEF>AUD</CURDEF>' in ofx_str
        assert '<STMTTRN>' in ofx_str
        assert '<FITID>' in ofx_str
        
        # Verify all transactions have FITIDs
        for txn in statement.transactions:
            assert txn.fitid is not None
            assert len(txn.fitid) <= 32  # OFX spec limit
            assert txn.fitid.startswith("ANZ_")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
