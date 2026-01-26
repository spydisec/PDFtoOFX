# PDF-to-OFX Converter - Complete Implementation Guide

## 1. Architecture Overview

```
┌─────────────────┐
│   Web UI        │
│  (FastAPI +     │
│   HTML/HTMX)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│        Application Layer                │
│  ┌──────────┐  ┌──────────┐            │
│  │ PDF      │  │ Template │            │
│  │ Detector │  │ Matcher  │            │
│  └──────────┘  └──────────┘            │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│      Extraction Layer                   │
│  ┌──────────┐  ┌──────────┐            │
│  │ Text     │  │ OCR      │            │
│  │ Extractor│  │ Extractor│            │
│  │(pdfplumber)│(tesseract)│            │
│  └──────────┘  └──────────┘            │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│      Processing Layer                   │
│  ┌──────────┐  ┌──────────┐            │
│  │ Parser   │  │ Normalizer│           │
│  │ (Template│  │ (FITID    │           │
│  │  Rules)  │  │  Generator)│          │
│  └──────────┘  └──────────┘            │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│      Verification Layer                 │
│  - Human review UI                      │
│  - Edit/approve transactions            │
│  - Balance validation                   │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│      Export Layer                       │
│  ┌──────────┐  ┌──────────┐            │
│  │ OFX v1   │  │ Duplicate│            │
│  │ Generator│  │ Checker  │            │
│  └──────────┘  └──────────┘            │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Actual Budget  │
│  (OFX Import)   │
└─────────────────┘
```

## 2. Data Flow

1. **Upload** → User uploads PDF + selects bank template + target account
2. **Detect** → System detects if PDF is text-based or scanned
3. **Extract** → Extract transactions using appropriate method
4. **Parse** → Apply bank template rules to normalize data
5. **Generate FITID** → Create stable transaction IDs
6. **Review** → User verifies/edits/approves transactions
7. **Export** → Generate OFX v1 SGML file
8. **Cleanup** → Delete uploaded PDF immediately
9. **Import** → User imports OFX into Actual Budget

## 3. Internal Transaction Schema

```python
class Transaction:
    """Normalized internal transaction model"""
    account_key: str          # e.g., "up_spending", "commbank_savings"
    statement_id: str         # sha256 hash of PDF bytes
    date_posted: str          # YYYY-MM-DD
    date_user: str | None     # YYYY-MM-DD (optional, for value date)
    amount: Decimal           # Signed decimal (negative for debit)
    trntype: str              # "DEBIT" or "CREDIT"
    memo: str                 # Cleaned description
    payee: str | None         # Extracted from memo
    fitid: str                # Stable unique ID (SHA1-based)
    balance: Decimal | None   # Running balance (if available)
    raw_row: dict             # Original extracted fields for audit
    approved: bool            # User approval status
    excluded: bool            # User marked for exclusion
```

## 4. FITID Generation Strategy

```python
def generate_fitid(
    bank_id: str,
    account_key: str,
    date_posted: str,
    amount: Decimal,
    memo: str,
    balance: Decimal | None = None,
    reference: str | None = None
) -> str:
    """
    Generate stable FITID for duplicate prevention.
    
    Priority:
    1. If statement provides reference number, use it directly
    2. Otherwise, hash key transaction attributes
    
    Hash includes:
    - Bank identifier
    - Account key
    - Date posted
    - Amount (to 2 decimal places)
    - Normalized memo (trimmed, lowercased)
    - Balance (if available, for extra stability)
    """
    if reference:
        # Use provided reference if available
        return reference
    
    # Normalize memo: remove extra spaces, lowercase
    normalized_memo = " ".join(memo.strip().lower().split())
    
    # Build hash components
    components = [
        bank_id,
        account_key,
        date_posted,
        f"{amount:.2f}",
        normalized_memo
    ]
    
    if balance is not None:
        components.append(f"{balance:.2f}")
    
    # Create SHA1 hash
    hash_input = "|".join(components).encode('utf-8')
    hash_output = hashlib.sha1(hash_input).hexdigest()
    
    # Use first 32 characters for reasonable uniqueness
    return hash_output[:32].upper()
```

## 5. Bank Template Configuration Schema

```yaml
# config/templates/up_bank.yaml
bank:
  name: "Up Bank"
  identifier: "up"
  default_bank_id: "000000"  # Up doesn't use traditional BSB
  
detection:
  # Text patterns to identify this bank's statement
  keywords:
    - "Up is a brand of Bendigo"
    - "up.com.au"
  
  # Page range to scan (0-indexed)
  transaction_pages:
    start: 0
    end: -1  # All pages
  
extraction:
  # For text-based PDFs
  text_mode:
    enabled: true
    # Table extraction settings
    table_settings:
      vertical_strategy: "lines"
      horizontal_strategy: "text"
      min_words_vertical: 1
      snap_tolerance: 3
    
    # Column identification
    columns:
      date: 
        patterns: ["\\d{1,2}(st|nd|rd|th)?\\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"]
        x_range: [0, 150]
      description:
        x_range: [150, 400]
      amount:
        patterns: ["\\$[\\d,]+\\.\\d{2}", "\\+\\$[\\d,]+\\.\\d{2}"]
        x_range: [400, 500]
      balance:
        patterns: ["\\$[\\d,]+\\.\\d{2}"]
        x_range: [500, 600]
  
  # For scanned PDFs
  ocr_mode:
    enabled: true
    preprocessing:
      - "grayscale"
      - "threshold"
      - "denoise"
    tesseract_config: "--psm 6"
    
parsing:
  date_format: "%A, %dth %b"  # e.g., "Wednesday, 21st Jan"
  secondary_date_format: "%dth %b"  # e.g., "21st Jan"
  
  amount_parsing:
    # Detect if amount has explicit sign
    positive_prefix: "+"
    negative_prefix: ""  # No prefix means debit for Up
    
    # If amount is in separate debit/credit columns
    debit_column: false
    credit_column: false
  
  memo_cleanup:
    # Rules to clean up description
    - pattern: "\\s+Round Up$"
      replacement: ""
    - pattern: "\\s+Direct Debit$"
      replacement: ""
    - pattern: "Zap Card \\*\\*\\d{4}"
      replacement: ""
  
  payee_extraction:
    # Extract payee from memo
    patterns:
      - "^([A-Z][\\w\\s&]+?)\\s+[A-Z]{2,}(?:\\s|$)"  # Up format
      - "^SQ \\*(.+?)\\s"  # Square payments
      - "^([\\w\\s]+?)\\s+\\d{10,}"  # Name before phone number
  
account_type_mapping:
  # Map Up account types to OFX ACCTTYPE
  "spending": "CHECKING"
  "saver": "SAVINGS"
  
statement_period:
  # Regex to extract statement period from PDF
  start_pattern: "Opening Balance.*?\\$(\\d+\\.\\d{2})"
  end_pattern: "Closing Balance.*?\\$(\\d+\\.\\d{2})"
  date_range_pattern: null  # Up doesn't show explicit date range in header
```

## 6. Technology Stack Justification

### Core Stack
- **Python 3.11+**: Latest stable, type hints, performance
- **FastAPI**: Modern, async, automatic API docs, WebSocket support
- **ofxtools**: Specialized OFX library, handles SGML format correctly
- **SQLite**: Lightweight, embedded, perfect for templates + import history

### PDF Extraction
- **pdfplumber** (PRIMARY): 
  - Excellent text extraction
  - Good table detection with customizable strategies
  - Access to character-level positioning
  - Active maintenance
  
- **Camelot** (ALTERNATIVE for complex tables):
  - Better for heavily formatted tables
  - Requires java/ghostscript dependencies
  - More setup overhead
  - **Decision: Use pdfplumber for MVP, add Camelot if needed**

- **tabula-py** (NOT CHOSEN):
  - Java dependency
  - Less Python-native
  - pdfplumber is more flexible

### OCR Stack
- **Tesseract 5+**: Industry standard, free, good AU English support
- **pytesseract**: Official Python wrapper
- **opencv-python**: Image preprocessing (denoise, threshold, deskew)
- **pdf2image**: Convert PDF pages to images for OCR

### Web UI
- **FastAPI + Jinja2 + HTMX**:
  - Minimal JavaScript
  - Progressive enhancement
  - Fast iteration
  - Server-side rendering
  
- **Alternative (NOT CHOSEN for MVP)**: React/Vue
  - Adds build complexity
  - Overkill for simple forms
  - Can add later if needed

## 7. File Structure

```
pdf-to-ofx/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── models.py               # Pydantic models
│   ├── config.py               # Settings
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── upload.py          # PDF upload endpoint
│   │   ├── review.py          # Transaction review endpoints
│   │   └── export.py          # OFX generation endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_detector.py    # Detect text vs scanned
│   │   ├── text_extractor.py  # pdfplumber extraction
│   │   ├── ocr_extractor.py   # Tesseract extraction
│   │   ├── parser.py          # Template-based parsing
│   │   ├── normalizer.py      # Transaction normalization
│   │   ├── fitid_generator.py # FITID generation
│   │   ├── ofx_generator.py   # OFX v1 SGML generation
│   │   └── template_manager.py# Load/match templates
│   ├── templates/             # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── upload.html
│   │   ├── review.html
│   │   └── components/
│   │       └── transaction_row.html
│   └── static/
│       ├── css/
│       └── js/
├── config/
│   ├── templates/             # Bank statement templates
│   │   ├── up_bank.yaml
│   │   ├── commbank.yaml
│   │   ├── anz.yaml
│   │   └── westpac.yaml
│   └── accounts.yaml          # User account mapping
├── data/
│   └── import_history.db      # SQLite for duplicate detection
├── tests/
│   ├── test_extractor.py
│   ├── test_parser.py
│   ├── test_fitid.py
│   └── test_ofx_generator.py
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## 8. MVP Implementation Plan

### Phase 1: Core Extraction (Week 1)
**Goal**: Extract transactions from text-based PDFs

1. **Setup project structure**
   ```bash
   pip install fastapi uvicorn pdfplumber python-multipart pydantic-settings
   ```

2. **Implement PDF detector**
   - Check if text extraction yields > 100 characters per page
   - Flag as text-based or scanned

3. **Implement text extractor (pdfplumber)**
   - Extract tables from PDF
   - Return raw rows with columns

4. **Create one bank template (Up Bank)**
   - YAML configuration
   - Date/amount/memo parsing rules

5. **Build parser**
   - Apply template rules
   - Normalize to Transaction model

6. **Test with provided PDF**
   - Verify all transactions extracted
   - Check date formats, amounts, memos

**Deliverable**: CLI tool that converts Up Bank PDF → JSON

### Phase 2: FITID & OFX Generation (Week 1)
**Goal**: Generate valid OFX files

1. **Implement FITID generator**
   - SHA1 hash of key fields
   - Handle collisions with counter suffix

2. **Implement OFX generator**
   - Use ofxtools OR manual SGML generation
   - Match provided OFX example structure
   - Set CURDEF=AUD, proper TRNAMT signs

3. **Test OFX validity**
   - Import into Actual Budget
   - Verify no errors
   - Test duplicate prevention (re-import same file)

**Deliverable**: CLI tool that converts PDF → OFX

### Phase 3: Web UI (Week 2)
**Goal**: User-friendly interface

1. **Build FastAPI app**
   - File upload endpoint
   - Session management (in-memory or Redis)

2. **Create upload page**
   - PDF upload form
   - Bank template selector
   - Account key input

3. **Create review page**
   - Show extracted transactions in table
   - Editable fields (date, amount, memo, trntype)
   - Checkbox for approval
   - "Approve all" button
   - Show totals: debits, credits, balance

4. **Create export endpoint**
   - Validate all approved
   - Generate OFX
   - Return file download
   - Delete uploaded PDF

5. **Add HTMX for interactivity**
   - Inline editing
   - Real-time validation
   - Progress indicators

**Deliverable**: Working web app for one bank

### Phase 4: Multi-Bank + OCR (Week 2-3)
**Goal**: Support multiple banks and scanned PDFs

1. **Add OCR extractor**
   - Install tesseract
   - Implement preprocessing pipeline
   - Extract text from images
   - Reconstruct table structure

2. **Create templates for major AU banks**
   - Commonwealth Bank
   - ANZ
   - Westpac
   - NAB
   - (Add more as needed)

3. **Implement template matcher**
   - Auto-detect bank from PDF content
   - Fall back to manual selection

4. **Add balance reconciliation**
   - Compare extracted ending balance vs calculated balance
   - Warn user if mismatch

**Deliverable**: Multi-bank support with OCR

### Phase 5: Polish + Production (Week 3-4)
**Goal**: Production-ready system

1. **Add import history tracking**
   - SQLite database
   - Store: statement_hash, date_range, account_key, imported_at
   - Warn on duplicate uploads

2. **Improve error handling**
   - Graceful failures
   - User-friendly error messages
   - Logging

3. **Add validation**
   - Required fields
   - Date format validation
   - Amount parsing validation
   - Duplicate FITID detection within statement

4. **Security**
   - File type validation (PDF only)
   - File size limits
   - Immediate file deletion
   - No persistent storage of financial data

5. **Testing**
   - Unit tests for each component
   - Integration tests
   - Test with real statements (redacted)

6. **Docker deployment**
   - Dockerfile
   - docker-compose.yml
   - Environment variables for config

**Deliverable**: Production-ready app with docs

## 9. Questions to Ask Before Finalizing Templates

### General
1. How many different banks/institutions will you need to support initially?
2. Are you comfortable sharing redacted sample PDFs for each bank?

### Per Bank
For each bank, I need:

1. **PDF Type**
   - Is the PDF text-selectable or scanned/image-based?
   - Can you copy-paste text from it?

2. **Transaction Table Layout**
   - What columns appear? (Date, Description, Debit, Credit, Balance, etc.)
   - Are debits and credits in separate columns or one signed column?
   - Is there a running balance column?

3. **Date Format**
   - What format? (DD/MM/YYYY, DD MMM YYYY, etc.)
   - Example: "26/01/2026" or "26 Jan 2026"

4. **Amount Format**
   - Signed (-$5.00) or unsigned ($5.00)?
   - Separate Dr/Cr columns?
   - Use of parentheses for debits: ($5.00)?

5. **Statement Period**
   - Where is the statement period shown?
   - Format of dates in header/footer?

6. **Reference Numbers**
   - Do transactions have reference/transaction IDs?
   - Where do they appear?
   - Example format?

7. **Account Identification**
   - What should be used as stable ACCTID?
     - Last 4 digits of account?
     - Full account number?
     - Internal nickname?
   - What is the account type? (Checking/Savings/Credit Card)

8. **Special Cases**
   - Any multi-line transaction descriptions?
   - Any summary sections to ignore?
   - Any fee transactions to handle specially?

## 10. Acceptance Criteria Checklist

- [ ] Upload PDF statement via web UI
- [ ] System auto-detects bank (or user selects manually)
- [ ] All transactions extracted and displayed
- [ ] User can edit any field (date, amount, memo, type)
- [ ] User can mark transactions for exclusion
- [ ] User must approve each transaction (or approve all)
- [ ] System validates all required fields filled
- [ ] System shows balance summary (debits/credits/total)
- [ ] Export generates valid OFX v1 SGML file
- [ ] OFX file contains correct:
  - [ ] CURDEF=AUD
  - [ ] TRNAMT signed correctly (negative for debit)
  - [ ] FITID for every transaction
  - [ ] Proper date format (YYYYMMDD)
  - [ ] Account details (BANKID, ACCTID, ACCTTYPE)
- [ ] OFX imports successfully into Actual Budget
- [ ] Re-importing same OFX does NOT create duplicates
- [ ] Uploaded PDF deleted immediately after export
- [ ] No financial data persisted after session ends
- [ ] Works with at least 2 different AU banks
- [ ] Handles both text-based and scanned PDFs
- [ ] Import history warns on duplicate uploads

## Next Steps

1. Review this implementation plan
2. Answer the questions in section 9 for each bank you need
3. Provide sample PDFs (redacted) for template creation
4. Approve tech stack and architecture
5. Begin Phase 1 implementation
