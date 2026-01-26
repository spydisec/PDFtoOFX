# Architecture Documentation

## System Overview

ANZ Plus to OFX Converter is a specialized tool for converting ANZ Plus bank statement PDFs to OFX v2.20 XML format for seamless import into Actual Budget and other personal finance applications.

### Design Philosophy

- **Simplicity:** Single-bank focus for reliability over broad compatibility
- **Accuracy:** Complete transaction preservation for balance integrity
- **Security:** Stateless, no persistence, in-memory processing
- **Usability:** Both web interface and CLI for different workflows

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   User Interface Layer                       │
│                                                              │
│  ┌─────────────────┐              ┌─────────────────┐      │
│  │  Web Interface  │              │   CLI Tool      │      │
│  │  (FastAPI +     │              │  (convert_pdf)  │      │
│  │   HTMX/Tailwind)│              └────────┬────────┘      │
│  └────────┬────────┘                       │               │
└───────────┼────────────────────────────────┼───────────────┘
            │                                │
            ▼                                ▼
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            PDF Text Extraction                        │  │
│  │            (pdfplumber)                               │  │
│  └─────────────────────┬────────────────────────────────┘  │
│                        ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         ANZ Plus Parser                               │  │
│  │  • Regex pattern matching                             │  │
│  │  • Multi-line description capture                     │  │
│  │  • Balance-based credit/debit detection               │  │
│  └─────────────────────┬────────────────────────────────┘  │
│                        ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Transaction Processing                        │  │
│  │  • Smart truncation (preserve merchant names)         │  │
│  │  • FITID generation (sequential counter)              │  │
│  │  • Data validation (Pydantic models)                  │  │
│  └─────────────────────┬────────────────────────────────┘  │
│                        ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         OFX Generation                                │  │
│  │         (ofxtools library)                            │  │
│  │  • OFX v2.20 XML format                               │  │
│  │  • Bank configuration                                 │  │
│  └────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Output / Export                              │
│  • OFX file download (web)                                  │
│  • OFX file save (CLI)                                      │
│  • Auto-cleanup (temp files)                                │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. PDF Extractor (`app/services/pdf_extractor.py`)

**Purpose:** Extract raw text from ANZ Plus PDF statements.

**Implementation:**
```python
def extract_text_from_pdf(pdf_path: Path) -> str:
    \"\"\"Extract text from all pages of PDF\"\"\"
    with pdfplumber.open(pdf_path) as pdf:
        text_parts = [page.extract_text() for page in pdf.pages]
    return "\\n".join(text_parts)
```

**Technology:** pdfplumber library
- Robust text extraction
- Character-level positioning
- Works with ANZ Plus digital PDFs

### 2. ANZ Plus Parser (`app/services/anz_plus_parser.py`)

**Purpose:** Parse ANZ Plus-specific transaction format from extracted text.

**Key Features:**

#### a) Multi-line Description Capture
```python
# Pattern matches main transaction line
TRANSACTION_PATTERN = r'^(\d{1,2})\s+([A-Z][a-z]{2})\s+(.+?)\s+\$?([\d,]+\.\d{2})(?:\s+\$?([\d,]+\.\d{2}))?$'

# Look ahead for continuation lines
while j < len(lines):
    next_line = lines[j].strip()
    if is_continuation(next_line):
        continuation_parts.append(next_line)
        j += 1
    else:
        break
```

**Example:**
```
PDF: 22 Jan VISA DEBIT PURCHASE CARD 1633 MYKI        $25.00
            PAYMENTS MELBOURNE

Result: "VISA DEBIT PURCHASE CARD 1633 MYKI PAYMENTS MELBOURNE"
```

#### b) Smart Truncation Algorithm
```python
def smart_truncate(description: str, max_len: int = 32) -> str:
    prefixes = [
        'VISA DEBIT PURCHASE CARD 1633 ',
        'EFTPOS ',
        'PAYMENT TO ',
    ]
    
    clean = description
    for prefix in prefixes:
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
            break
    
    return clean[:max_len] if len(clean) > max_len else clean
```

**Result:** OFX NAME field shows `MYKI PAYMENTS MELBOURNE` instead of truncated `VISA DEBIT PURCHASE CARD 1633 MY`

#### c) Balance-based Credit/Debit Detection
```python
def _determine_transaction_type(
    current_balance: Decimal,
    balance_after: Decimal,  # Chronologically AFTER this transaction
    amount: Decimal
) -> TransactionType:
    # PDFs show newest→oldest, so we compare forward in time
    balance_change = balance_after - current_balance
    
    if balance_change < 0:
        return TransactionType.DEBIT  # Balance decreased = money out
    elif balance_change > 0:
        return TransactionType.CREDIT  # Balance increased = money in
    
    # Fallback to keyword detection
    ...
```

**Why this works:**
- More reliable than keyword matching
- Handles edge cases (refunds, reversals)
- Works even with unfamiliar transaction types

### 3. FITID Generator (`app/services/fitid_generator.py`)

**Purpose:** Generate unique, collision-free Financial Transaction IDs for duplicate detection.

**Strategy:** Sequential counter format

```python
def generate_fitid(date: date, counter: int) -> str:
    return f"ANZ_{date.strftime('%Y%m%d')}_{counter:04d}"
```

**Examples:**
- `ANZ_20260122_0001`
- `ANZ_20260122_0002`
- `ANZ_20260123_0001`

**Advantages:**
- Simple and predictable
- No hash collisions
- Easy debugging
- Stable across re-imports

### 4. OFX Generator (`app/services/ofx_generator.py`)

**Purpose:** Convert parsed transactions to OFX v2.20 XML format.

**Implementation:**
```python
def generate(self, statement: Statement) -> bytes:
    # Create OFX objects
    stmttrn_list = []
    for txn in statement.transactions:
        stmttrn = STMTTRN(
            trntype=txn.transaction_type.value,
            dtposted=txn.date.strftime('%Y%m%d'),
            trnamt=txn.amount if txn.transaction_type == TransactionType.CREDIT else -txn.amount,
            fitid=txn.fitid,
            name=txn.name,
            memo=txn.memo
        )
        stmttrn_list.append(stmttrn)
    
    # Generate OFX XML
    return ofx.to_xml(version=220)
```

**Technology:** ofxtools library
- Handles OFX spec complexity
- Validates XML structure
- Supports both SGML v1 and XML v2

### 5. Data Models (`app/models.py`)

**Purpose:** Type-safe data structures using Pydantic.

```python
class Transaction(BaseModel):
    date: date
    description: str
    amount: Decimal
    transaction_type: TransactionType  # DEBIT or CREDIT
    balance: Optional[Decimal] = None
    fitid: Optional[str] = None
    name: str  # Truncated for OFX NAME field (32 chars)
    memo: str  # Full description for OFX MEMO field

class Statement(BaseModel):
    account_name: str
    account_number: str
    opening_balance: Optional[Decimal]
    closing_balance: Optional[Decimal]
    date_start: date
    date_end: date
    transactions: List[Transaction]
```

## Web Application Architecture

### FastAPI + HTMX Pattern

```
┌────────────────────────────────────────┐
│  Browser                               │
│  ├── HTML (Jinja2 templates)          │
│  ├── CSS (Tailwind CDN)               │
│  └── HTMX (dynamic interactions)      │
└────────┬───────────────────────────────┘
         │ HTTP
         ▼
┌────────────────────────────────────────┐
│  FastAPI Server                        │
│  ├── / (GET) → index.html             │
│  ├── /convert (POST) → HTML response  │
│  └── /download/{file} (GET) → OFX     │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  Conversion Pipeline                   │
│  (same as CLI)                         │
└────────────────────────────────────────┘
```

**Key Design Decisions:**

1. **HTMX over JavaScript frameworks**
   - Zero build step
   - Progressive enhancement
   - Server-side rendering
   - Simpler debugging

2. **Tailwind CSS via CDN**
   - No build process
   - Rapid prototyping
   - Consistent design system

3. **Stateless architecture**
   - No database
   - Files in memory
   - Auto-cleanup after download

4. **Background tasks**
   ```python
   FileResponse(
       path=ofx_path,
       background=BackgroundTask(cleanup_file, ofx_path)
   )
   ```

## Data Flow

### CLI Conversion Flow

```
1. User runs: python convert_pdf.py input.pdf output.ofx
                         ↓
2. PDF Extractor: extract_text_from_pdf(input.pdf) → raw_text
                         ↓
3. ANZ Plus Parser: parse(raw_text) → Statement object
                         ↓
4. FITID Generator: Assign unique IDs to transactions
                         ↓
5. OFX Generator: generate(statement) → OFX XML bytes
                         ↓
6. File Writer: Save to output.ofx
                         ↓
7. Complete: Display summary (count, date range, balances)
```

### Web Conversion Flow

```
1. User uploads PDF via drag-and-drop
                         ↓
2. Browser: HTMX POST to /convert with multipart/form-data
                         ↓
3. FastAPI: Save to temp file
                         ↓
4. [Same conversion pipeline as CLI]
                         ↓
5. FastAPI: Return HTML with download button + summary
                         ↓
6. User clicks download
                         ↓
7. FastAPI: Stream OFX file, cleanup in background
```

## Security Considerations

### 1. File Handling
- **Validation:** Only accept `.pdf` files, max 10MB
- **Sanitization:** Filename sanitization to prevent path traversal
- **Temp files:** Use system temp directory with unique names
- **Cleanup:** Auto-delete after 1 hour or after download

### 2. No Persistence
- **Stateless:** No database, no user accounts
- **Privacy:** Files deleted immediately after processing
- **Memory-only:** Conversion happens in memory where possible

### 3. Input Validation
```python
# File type check
if not file.filename.lower().endswith('.pdf'):
    raise HTTPException(400, "Only PDF files supported")

# Size limit
if len(content) > 10 * 1024 * 1024:
    raise HTTPException(400, "File too large (max 10MB)")

# Filename sanitization
if '/' in filename or '\\' in filename or '..' in filename:
    raise HTTPException(400, "Invalid filename")
```

## Performance Characteristics

### PDF Processing
- **Small statements** (10-20 transactions): <1 second
- **Medium statements** (50-100 transactions): 1-2 seconds
- **Large statements** (200+ transactions): 2-4 seconds

**Bottlenecks:**
- PDF text extraction (pdfplumber)
- Multi-line description parsing (regex)

### Web App
- **Page load:** <500ms (Tailwind CSS via CDN)
- **File upload:** Depends on file size + network
- **Conversion:** Same as CLI processing time
- **Download:** Instant (file already generated)

### Memory Usage
- **Typical:** 50-100MB per conversion
- **Peak:** 200MB for large PDFs
- **Cleanup:** Automatic garbage collection

## Error Handling

### Graceful Degradation

```python
try:
    text = extract_text_from_pdf(pdf_path)
except PDFException:
    return "Could not extract text. PDF may be scanned or corrupted."

try:
    statement = parser.parse(text)
except ParsingException as e:
    return f"Could not parse transactions: {str(e)}"

try:
    ofx_content = generator.generate(statement)
except OFXException as e:
    return f"Could not generate OFX: {str(e)}"
```

### User-Friendly Messages

Web interface shows:
- ✅ Success: Transaction count, date range, balances
- ❌ Error: Clear message about what went wrong
- 💡 Suggestion: "Ensure this is an ANZ Plus digital PDF"

## Testing Strategy

### Unit Tests
```python
test_fitid_generator.py:
  ✓ Sequential counter with no collisions
  ✓ Different dates have independent counters
  ✓ Reference number priority

test_anz_plus_parser.py:
  ✓ Parse transaction line correctly
  ✓ Multi-line descriptions captured
  ✓ All transactions preserved (no filtering)
  
test_converter.py:
  ✓ End-to-end conversion produces valid OFX
```

### Test Coverage
- **Target:** >90%
- **Current:** 91%
- **Critical paths:** 100% coverage (parser, generator)

## Future Extensibility

### Supporting Additional Banks

**Architecture allows:**
1. Create new parser class (e.g., `CommBankParser`)
2. Implement same interface as `AnzPlusParser`
3. Add bank detection logic
4. Register in router

**Example:**
```python
class CommBankParser:
    def parse(self, text: str) -> Statement:
        # CommBank-specific parsing logic
        ...

# In routes.py
if "commbank" in text.lower():
    parser = CommBankParser()
else:
    parser = AnzPlusParser()
```

### Adding OCR Support

**For scanned PDFs:**
1. Add `pdf2image` + `pytesseract` dependencies
2. Detect if PDF is image-based
3. Convert pages to images
4. Run OCR
5. Parse extracted text (same pipeline)

### Batch Processing

**Web interface enhancement:**
1. Accept multiple files
2. Process in parallel (asyncio)
3. Zip OFX files for download
4. Progress bar for multiple files

## Technology Stack

| Component | Technology | Why? |
|-----------|-----------|------|
| **Language** | Python 3.11+ | Type hints, performance, ecosystem |
| **Web Framework** | FastAPI | Async, auto docs, modern |
| **Server** | Uvicorn | ASGI, fast, WebSocket support |
| **PDF Extraction** | pdfplumber | Best text extraction, active maintenance |
| **OFX Generation** | ofxtools | Specialized library, handles v1 & v2 |
| **Data Validation** | Pydantic | Type safety, automatic validation |
| **Templates** | Jinja2 | Django-like, powerful |
| **CSS** | Tailwind (CDN) | Utility-first, no build step |
| **Interactivity** | HTMX | Zero JavaScript, progressive enhancement |
| **Testing** | pytest | De facto standard, excellent plugins |

## Deployment Architecture

### Development
```bash
python run_web.py  # Auto-reload, debug mode
```

### Production Options

**Option 1: Docker**
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "app.web.main:app", "--host", "0.0.0.0"]
```

**Option 2: Cloud Platform**
- Render.com: Free tier, auto-deploy
- Railway.app: $5/month, easy setup
- Fly.io: Global edge, pay-as-you-go

## Conclusion

This architecture prioritizes:
- **Simplicity** over complexity
- **Reliability** over features
- **User experience** over technical elegance
- **Maintainability** over optimization

The single-bank focus allows deep specialization in ANZ Plus parsing, resulting in higher accuracy and easier maintenance than a generic multi-bank solution.
