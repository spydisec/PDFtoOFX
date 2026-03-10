#!/usr/bin/env python3
"""
ANZ Plus PDF to OFX Converter

Converts ANZ Plus bank statement PDFs to OFX format for import into Actual Budget.
Specifically designed for ANZ Plus digital statement format.
"""
import sys
from pathlib import Path

from app.services.anz_plus_parser import AnzPlusParser
from app.services.ofx_generator import OFXGenerator
from app.models import BankConfig


def main():
    """Main CLI function"""
    if len(sys.argv) < 2:
        print("Usage: python convert_pdf.py <input.pdf> [output.ofx]")
        print("\nConverts ANZ Plus PDF statements to OFX format")
        print("Example: python convert_pdf.py statement.pdf output.ofx")
        print()
        print("Example:")
        print("  python convert_pdf.py statement.pdf")
        print("  python convert_pdf.py statement.pdf output.ofx")
        sys.exit(1)
    
    # Get input/output paths
    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)
    
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    else:
        # Default output: same name with .ofx extension
        output_path = input_path.with_suffix('.ofx')
    
    print(f"Converting: {input_path}")
    print(f"Output to: {output_path}")
    print()
    
    try:
        # Step 1: Parse PDF
        print("Step 1: Parsing PDF...")
        parser = AnzPlusParser()
        statement = parser.parse_pdf(input_path)
        print(f"  ✓ Found {len(statement.transactions)} transactions")
        print(f"  ✓ Date range: {statement.date_start} to {statement.date_end}")
        if statement.opening_balance:
            print(f"  ✓ Opening balance: ${statement.opening_balance}")
        if statement.closing_balance:
            print(f"  ✓ Closing balance: ${statement.closing_balance}")
        
        # Step 2: Generate OFX
        print("Step 2: Generating OFX file...")
        bank_config = BankConfig(
            name="ANZ Plus",
            ofx_version=220,  # OFX v2.20 XML format
            bank_id="633-123",
            currency="AUD"
        )
        generator = OFXGenerator(bank_config)
        ofx_content = generator.generate(statement)
        print(f"  ✓ Generated {len(ofx_content)} bytes of OFX data")
        
        # Step 3: Write to file
        print("Step 3: Writing OFX file...")
        output_path.write_bytes(ofx_content)
        print(f"  ✓ Saved to {output_path}")
        
        print()
        print("✅ Conversion complete!")
        print()
        print("Next steps:")
        print("  1. Import the OFX file into Actual Budget")
        print("  2. Verify transactions match your PDF")
        print("  3. Re-import the same file to test duplicate detection")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
