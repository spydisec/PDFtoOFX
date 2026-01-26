# ANZ Plus PDF to OFX Converter

Convert ANZ Plus bank statement PDFs to OFX format for import into Actual Budget and other personal finance applications.

[![Tests](https://img.shields.io/badge/tests-6%2F6%20passing-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

## Features

✅ **Multi-line Description Capture** - Extracts complete transaction details including merchant, location, and reference numbers  
✅ **Smart Truncation** - Preserves merchant names in 32-character NAME field by removing common prefixes  
✅ **Accurate Credit/Debit Detection** - Uses balance change analysis for reliable transaction type identification  
✅ **Collision-free FITIDs** - Sequential counter strategy ensures unique transaction IDs for duplicate detection  
✅ **OFX v2.20 XML Format** - Compatible with Actual Budget and other modern finance applications  
✅ **Complete Transaction History** - Converts all transactions without filtering to maintain accurate balances

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/PDFtoOFX.git
cd PDFtoOFX

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### Web Interface (Recommended)

Run the elegant web interface with drag-and-drop file upload:

```bash
python run_web.py
```

Then open your browser to **http://localhost:8000**

**Features:**
- 🎨 Minimalistic, elegant design with Tailwind CSS
- 📤 Drag-and-drop PDF upload
- ⚡ Instant conversion with progress indicators
- 📥 One-click OFX download
- 🔒 Secure (files processed in memory, auto-deleted)
- 📱 Mobile responsive

### Command Line Interface

```bash
python convert_pdf.py input.pdf output.ofx
```

**Example:**
```bash
python convert_pdf.py examples/pdfs/sample_anz_plus.pdf my_statement.ofx
```

**Output:**
```
Converting: examples/pdfs/sample_anz_plus.pdf
Output to: my_statement.ofx

Step 1: Extracting text from PDF...
  ✓ Extracted 5438 characters
Step 2: Parsing transactions...
  ✓ Found 26 transactions
  ✓ Date range: 2026-01-02 to 2026-01-22
  ✓ Opening balance: $3117.92
  ✓ Closing balance: $232.16
Step 3: Generating OFX file...
  ✓ Generated 8661 bytes of OFX data
Step 4: Writing OFX file...
  ✓ Saved to my_statement.ofx

✅ Conversion complete!
```

### Import into Actual Budget

1. Open Actual Budget
2. Navigate to your account
3. Click **Import** → **Select File**
4. Choose your `.ofx` file
5. Review and approve transactions

### Verify Duplicate Detection

Re-import the same OFX file to confirm that all transactions are detected as duplicates. This validates that the FITID strategy is working correctly.

## Supported Bank

This converter is **specifically designed for ANZ Plus** bank statement PDFs. It parses the unique transaction format used by ANZ Plus digital statements.

**Supported Format:**
- ANZ Plus digital PDF statements
- Transaction list format with Date, Description, Credit, Debit, Balance columns
- Multi-line transaction details

**Not Supported:**
- Other ANZ products (ANZ Classic, ANZ Access, etc.) - different PDF formats
- Scanned/image PDFs - requires OCR functionality
- Other banks - requires bank-specific parsers

## Example Transaction Output

**ANZ Plus PDF:**
```
22 Jan VISA DEBIT PURCHASE CARD 1633 MYKI        $25.00    $233.45
       PAYMENTS MELBOURNE
```

**Generated OFX:**
```xml
<STMTTRN>
  <TRNTYPE>DEBIT</TRNTYPE>
  <DTPOSTED>20260122000000.000[+0:UTC]</DTPOSTED>
  <TRNAMT>-25.00</TRNAMT>
  <FITID>ANZ_20260122_0001</FITID>
  <NAME>MYKI PAYMENTS MELBOURNE</NAME>
  <MEMO>VISA DEBIT PURCHASE CARD 1633 MYKI PAYMENTS MELBOURNE</MEMO>
</STMTTRN>
```

**Improvements:**
- **NAME field:** `MYKI PAYMENTS MELBOURNE` (smart truncation - merchant visible)
- **MEMO field:** Full description with location details
- **Type:** Correctly identified as DEBIT using balance analysis
- **FITID:** `ANZ_20260122_0001` (sequential counter, collision-free)

## Project Structure

```
PDFtoOFX/
├── run_web.py               # Web app launcher
├── convert_pdf.py           # CLI tool
├── app/
│   ├── models.py            # Pydantic data models
│   ├── web/                 # Web application
│   │   ├── main.py          # FastAPI app
│   │   ├── routes.py        # API endpoints
│   │   └── templates/       # HTML templates (Tailwind + HTMX)
│   └── services/
│       ├── anz_plus_parser.py   # ANZ Plus PDF parser
│       ├── fitid_generator.py   # Unique ID generation
│       ├── ofx_generator.py     # OFX XML builder
│       └── pdf_extractor.py     # PDF text extraction
├── tests/
│   └── test_converter.py    # Test suite (91% coverage)
├── docs/
│   ├── QUICKSTART.md        # Detailed usage guide
│   ├── IMPLEMENTATION_GUIDE.md  # Technical implementation
│   ├── WEB_APP_PLAN.md      # Web app architecture
│   └── DEVELOPMENT.md       # Contributing guide
└── examples/
    ├── pdfs/                # Sample ANZ Plus PDFs
    └── outputs/             # Example OFX files
```

## Requirements

- Python 3.11 or higher
- Dependencies (see [requirements.txt](requirements.txt)):
  - `ofxtools>=0.9.6` - OFX file generation
  - `pdfplumber>=0.11.0` - PDF text extraction
  - `pydantic>=2.5.3` - Data validation
  - `python-dateutil>=2.9.0` - Date parsing
  - `fastapi>=0.109.0` - Web framework
  - `uvicorn>=0.27.0` - ASGI server
  - `jinja2>=3.1.3` - Template rendering

## Development

### Run Tests

```bash
pytest tests/ -v
```

### Run with Code Coverage

```bash
pytest tests/ --cov=app --cov-report=html
```

### Web App Development

```bash
# Run with auto-reload on code changes
python run_web.py

# Or use uvicorn directly
uvicorn app.web.main:app --reload --port 8000
```

## Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Detailed installation and usage
- **[Implementation Guide](docs/IMPLEMENTATION_GUIDE.md)** - Technical architecture
- **[Development Guide](docs/DEVELOPMENT.md)** - Contributing to the project
- **[Project Summary](docs/PROJECT_SUMMARY.md)** - Original project documentation

## Testing

```bash
# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=term-missing
```

**Test Results:**
```
✅ 6/6 tests passing
✅ 91% code coverage
✅ FITID collision detection verified
✅ Multi-line description capture validated
✅ Smart truncation tested
```

## How It Works

### 1. PDF Text Extraction
Uses `pdfplumber` to extract text from ANZ Plus PDF statements.

### 2. Transaction Parsing
Custom regex patterns parse the ANZ Plus transaction format:
- Date and month (e.g., "22 Jan")
- Multi-line descriptions (merchant, location, reference)
- Amounts and balances
- Filters out ROUND UP micro-savings

### 3. Smart Truncation
Strips common prefixes before 32-character truncation:
- `VISA DEBIT PURCHASE CARD 1633` → merchant name
- `EFTPOS` → merchant name
- `PAYMENT TO` → payee name

### 4. Credit/Debit Detection
Priority-based detection:
1. **Balance change analysis** (most reliable) - compares chronological balance changes
2. **Keyword detection** - expanded lists for CREDIT and DEBIT transactions
3. **Default to DEBIT** - conservative fallback

### 5. FITID Generation
Sequential counter format: `ANZ_YYYYMMDD_NNNN`
- Guarantees no collisions
- Enables reliable duplicate detection
- Works across multiple imports

### 6. OFX Generation
Uses `ofxtools` library to generate valid OFX v2.20 XML format compatible with Actual Budget.

## Known Limitations

- **ANZ Plus Only** - Currently only supports ANZ Plus PDF format
- **Digital PDFs** - Does not support scanned/image PDFs (OCR not implemented)
- **Manual Year** - Parser uses current year (can be overridden if needed)
- **Single Bank** - Multi-bank support requires bank-specific parsers

## Future Enhancements

- [ ] Support for other ANZ products
- [ ] Support for other Australian banks (CommBank, Westpac, NAB, Up Bank)
- [ ] OCR support for scanned PDFs
- [ ] Web interface for easy uploads
- [ ] Batch processing for multiple statements
- [ ] Docker container for easy deployment

## Contributing

Contributions are welcome! Please see [DEVELOPMENT.md](docs/DEVELOPMENT.md) for:
- Development setup
- Code style guidelines
- Testing requirements
- Pull request process

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [ofxtools](https://github.com/csingley/ofxtools) for OFX generation
- PDF parsing powered by [pdfplumber](https://github.com/jsvine/pdfplumber)
- Designed for [Actual Budget](https://actualbudget.com/) compatibility

## Support

For issues, questions, or feature requests:
- Open an [issue](https://github.com/yourusername/PDFtoOFX/issues)
- Check [existing documentation](docs/)
- Review [example files](examples/)

---

**Note:** This project is not affiliated with ANZ Bank. It is an independent tool created for personal finance management.
