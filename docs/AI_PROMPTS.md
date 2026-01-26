# 🤖 AI-Assisted Implementation Guide
## PDF to OFX Converter - Phase-by-Phase Prompts

This guide provides **exact prompts** to use with **GitHub Copilot** and **Claude 4.5** to build the PDF-to-OFX converter step-by-step in VSCode.

---

## 📋 Pre-Implementation Setup

### Initial VSCode Setup Prompt

```
I'm building a PDF-to-OFX converter for Australian bank statements in Python using VSCode.

Tech stack:
- Python 3.11+
- FastAPI for web framework
- pdfplumber for PDF extraction
- Pydantic for data validation
- Will support Actual Budget OFX import

Help me set up the project structure:
1. Create a professional .gitignore for Python/FastAPI
2. Set up virtual environment (venv)
3. Create initial directory structure:
   - app/ (main application code)
   - app/services/ (business logic)
   - app/templates/ (HTML templates)
   - tests/ (unit tests)
   - config/ (bank templates)
   - docs/ (documentation)

Show me the commands to run and file structure to create.
```

---

## 🏗️ PHASE 1: Project Foundation & Core Models

**Goal**: Set up project structure, create data models, no web UI yet.

### 1.1 - Create requirements.txt

**Prompt for Copilot/Claude:**
```
Create a requirements.txt file for a Python 3.11+ PDF-to-OFX converter with these dependencies:

Required packages:
- FastAPI with uvicorn (web framework)
- pdfplumber (PDF text extraction)
- pytesseract (OCR for scanned PDFs)
- opencv-python (image preprocessing)
- pdf2image (PDF to image conversion)
- Pydantic v2 (data validation)
- python-multipart (file uploads)
- jinja2 (HTML templates)

Development packages:
- pytest and pytest-asyncio (testing)
- httpx (FastAPI testing)

Production packages:
- gunicorn (production server)

Pin all versions for reproducibility. Add helpful comments.
```

### 1.2 - Create Core Data Models

**Prompt for Copilot/Claude:**
```
Create app/models.py with Pydantic v2 models for a PDF-to-OFX converter.

Required models:
1. Transaction model with:
   - account_key: str (user-assigned identifier)
   - statement_id: str (hash of PDF)
   - date_posted: date
   - date_user: Optional[date]
   - amount: Decimal (signed, negative for debits)
   - trntype: Enum["DEBIT", "CREDIT"]
   - memo: str (description)
   - payee: Optional[str]
   - fitid: str (stable unique ID)
   - balance: Optional[Decimal]
   - raw_row: dict (original data)
   - approved: bool = False
   - excluded: bool = False

2. Statement model with:
   - statement_id, bank_name, account_key
   - account_id, bank_id, account_type
   - date_start, date_end
   - opening_balance, closing_balance
   - transactions: list[Transaction]
   - Properties: total_debits, total_credits, calculated_balance, balance_matches

3. AccountType enum: CHECKING, SAVINGS, CREDITLINE

Add field validators for amounts (round to 2 decimals) and memos (not empty).
Include docstrings and type hints.
```

### 1.3 - Test Models

**Testing Prompt:**
```
Create tests/test_models.py to test the Transaction and Statement models.

Test cases:
1. Valid transaction creation
2. Amount rounding to 2 decimals
3. Empty memo validation (should fail)
4. Statement total_debits calculation
5. Statement total_credits calculation
6. Balance matching logic

Use pytest fixtures for sample data.
Show me how to run: pytest tests/test_models.py -v
```

**✅ Checkpoint**: Run `pytest tests/test_models.py -v` - All tests should pass before moving to Phase 2.

---

## ⚙️ PHASE 2: FITID Generation & OFX Output

**Goal**: Generate stable transaction IDs and create valid OFX files.

### 2.1 - FITID Generator

**Prompt for Copilot/Claude:**
```
Create app/services/fitid_generator.py that generates stable, unique transaction IDs.

Requirements:
1. Class: FITIDGenerator with method generate()
2. Parameters: bank_id, account_key, date_posted (str YYYY-MM-DD), amount (Decimal), memo (str), balance (Optional[Decimal]), reference (Optional[str])
3. Logic:
   - Priority 1: If reference provided, use it directly (cleaned)
   - Priority 2: Generate SHA1 hash of: bank_id + account_key + date + amount + normalized_memo + balance
   - Normalize memo: lowercase, remove extra spaces
   - Use first 32 chars of hash in uppercase
   - Handle collisions: track FITIDs in dict, append -01, -02 if duplicate
4. Include reset() method to clear collision counter

Add comprehensive docstrings and usage example in __main__ block.
```

### 2.2 - OFX v1 SGML Generator

**Prompt for Copilot/Claude:**
```
Create app/services/ofx_generator.py that generates OFX v1.02 SGML files.

CRITICAL FORMAT REQUIREMENTS (from example OFXData.ofx):
- Header format: OFXHEADER:100, DATA:OFXSGML, VERSION:102 (NOT XML)
- SGML tags without closing slashes (e.g., <TRNTYPE>DEBIT, not <TRNTYPE>DEBIT</TRNTYPE>)
- Always set CURDEF to AUD
- TRNAMT must be signed: negative for debits, positive for credits
- Date format: YYYYMMDD for dates, YYYYMMDDHHMMSS for datetimes
- Every transaction must have FITID

Create class OFXGenerator with methods:
1. generate_header() -> str (OFX header section)
2. generate_signon() -> str (signon message)
3. generate_transaction(txn: Transaction) -> str (single STMTTRN block)
4. generate_statement(statement: Statement) -> str (complete OFX file)
5. save_to_file(statement: Statement, output_path: str)

Include escape_sgml() for special characters (&, <, >).
Add example usage in __main__ that creates a sample OFX file.
```

### 2.3 - Test FITID & OFX

**Testing Prompt:**
```
Create tests/test_fitid_generator.py and tests/test_ofx_generator.py

Test FITID Generator:
1. Same inputs produce same FITID (stability)
2. Different inputs produce different FITIDs (uniqueness)
3. Reference number takes priority
4. Collision handling (duplicate transactions on same day)
5. Balance inclusion in hash

Test OFX Generator:
1. Header format matches OFX v1 SGML (not XML)
2. CURDEF is AUD
3. Debit amounts are negative
4. Credit amounts are positive
5. FITID present in every transaction
6. Valid SGML structure (no closing slashes)

Show commands to run tests individually and together.
```

**✅ Checkpoint**: 
```bash
pytest tests/test_fitid_generator.py -v
pytest tests/test_ofx_generator.py -v
python app/services/ofx_generator.py  # Should create sample .ofx file
```

Manually inspect the generated OFX file - it should match the example OFXData.ofx structure exactly.

---

## 📄 PHASE 3: PDF Extraction & Parsing

**Goal**: Extract transactions from PDF statements.

### 3.1 - PDF Text Extractor

**Prompt for Copilot/Claude:**
```
Create app/services/text_extractor.py for extracting text from PDF statements.

Requirements:
1. Class: PDFTextExtractor - use as context manager (with statement)
2. __init__(pdf_path: str)
3. Methods:
   - detect_text_pdf() -> bool: Check if PDF has extractable text (>100 chars/page avg)
   - extract_text_from_page(page_num: int) -> str
   - extract_tables_from_page(page_num: int, table_settings: dict) -> List[List[str]]
   - extract_all_tables(start_page: int, end_page: Optional[int]) -> List[List[str]]
   - extract_with_positions(page_num: int) -> List[Dict]: Get words with x,y coordinates

4. Static utility methods:
   - parse_amount(text: str) -> Optional[Decimal]: Handle $42.00, -$42.00, ($42.00), $1,234.56
   - parse_date(text: str, date_formats: List[str]) -> Optional[datetime]: Try multiple formats, remove ordinal suffixes (1st, 2nd)

Use pdfplumber library. Include detailed docstrings.
Add __main__ example that analyzes a PDF and shows:
- Is text-based?
- Sample extracted text
- Sample table rows
- Sample amounts/dates parsed
```

### 3.2 - Up Bank Parser (Template Example)

**Prompt for Copilot/Claude:**
```
Create app/services/up_bank_parser.py for parsing Up Bank PDF statements.

Up Bank format (from example PDF):
- Date line: "Wednesday, 21st Jan"
- Next line: "6:58pm Description text with merchant"
- Next line: "Round Up Direct Debit $42.00" (transaction type + amount)
- Next line: "$280.48" (running balance)
- No explicit Dr/Cr columns - amounts without + are debits
- Credits have "+" prefix or contain "Credit"/"Deposit"

Class: UpBankParser
- BANK_NAME = "Up Bank"
- BANK_ID = "000000"
- KEYWORDS = ["Up is a brand of Bendigo", "up.com.au"]
- DATE_FORMATS = ["%A, %d %b", "%d %b", "%d/%m/%Y"]
- MEMO_CLEANUP_PATTERNS: remove "Round Up", "Direct Debit", "Zap Card **XXXX"
- PAYEE_PATTERNS: regex to extract merchant/payee name

Methods:
1. __init__(pdf_path: str)
2. detect_bank(pdf_text: str) -> bool
3. parse_statement(account_key: str) -> Statement:
   - Calculate statement_id (SHA256 of PDF)
   - Extract balances from "Opening Balance $X" and "Closing Balance $Y"
   - Extract date range from "January 2026 Interim Statement"
   - Parse transactions line by line
   - Generate FITIDs
   - Return Statement object

4. _parse_single_transaction(lines, start_index, account_key, statement_id) -> Optional[Transaction]
5. _clean_memo(memo: str) -> str
6. _extract_payee(memo: str) -> Optional[str]

Add __main__ block that parses a sample Up Bank PDF and prints:
- Statement period
- Opening/closing balance
- Transaction count
- First 5 transactions
- Balance match check
```

### 3.3 - Test PDF Extraction

**Testing Prompt:**
```
Create tests/test_text_extractor.py and tests/test_up_bank_parser.py

For text_extractor:
1. Test amount parsing: "$42.00" -> Decimal("-42.00")
2. Test amount parsing: "+$100.00" -> Decimal("100.00")
3. Test amount parsing: "($50.00)" -> Decimal("-50.00")
4. Test amount parsing: "$1,234.56" -> Decimal("-1234.56")
5. Test date parsing with ordinals: "21st Jan" -> date object

For up_bank_parser (using fixture PDF):
1. Test bank detection
2. Test balance extraction
3. Test transaction parsing
4. Test FITID generation
5. Test payee extraction

Create a sample_statements/ directory with redacted test PDFs.
```

**✅ Checkpoint**:
```bash
pytest tests/test_text_extractor.py -v
python app/services/up_bank_parser.py  # Should parse real Up Bank PDF
```

Manually verify: Does it extract all transactions? Are amounts signed correctly? Do balances match?

---

## 🌐 PHASE 4: FastAPI Web Application

**Goal**: Build the web interface for upload, review, and export.

### 4.1 - Create FastAPI App Structure

**Prompt for Copilot/Claude:**
```
Create app/main.py - a FastAPI application for PDF-to-OFX conversion.

Structure:
1. FastAPI app initialization with CORS
2. In-memory session storage: Dict[session_id, {statement, pdf_path, temp_dir, uploaded_at}]
3. Jinja2Templates for HTML rendering

Routes to create:
- GET / -> upload.html (upload form)
- POST /upload -> Process PDF, return session_id + statement data
- GET /review/{session_id} -> review.html (show transactions)
- POST /review/{session_id}/update -> Update single transaction
- POST /review/{session_id}/approve-all -> Approve all transactions
- GET /export/{session_id} -> Generate OFX, return file download, cleanup
- DELETE /session/{session_id} -> Cancel and cleanup
- GET /health -> Health check endpoint

Requirements:
- Upload validation: PDF only, size limit
- Temporary file handling: Create temp dir, store PDF
- Session ID: First 16 chars of PDF SHA256 hash
- Cleanup: Delete PDF and temp dir after export
- Error handling: HTTPException with clear messages

Use tempfile module for temp directories.
Include comprehensive error handling and logging.
```

### 4.2 - Create Upload Page Template

**Prompt for Copilot/Claude:**
```
Create app/templates/upload.html - Professional upload page.

Requirements:
1. Modern, clean design with gradient background
2. Form fields:
   - Account name (text input with placeholder)
   - Bank selector (dropdown: Up Bank, others disabled/coming soon)
   - PDF file upload with drag-and-drop area
3. Visual feedback:
   - File name display after selection
   - Loading spinner during upload
   - Error messages in styled box
4. Use HTMX for AJAX submission (https://unpkg.com/htmx.org@1.9.10)
5. JavaScript for:
   - File input change handler
   - Form submission
   - Redirect to review page on success

Design style:
- Professional gradient (purple/blue)
- Card-based layout with shadows
- Responsive design
- Clear typography
- Icons for upload area (SVG)

No external CSS frameworks - use inline <style> tag.
```

### 4.3 - Create Review Page Template

**Prompt for Copilot/Claude:**
```
Create app/templates/review.html - Interactive transaction review page.

Requirements:
1. Header section showing:
   - Bank name, account, date range, transaction count
   - Summary boxes grid layout
2. Warnings section (if balance mismatch or unapproved transactions)
3. Action buttons:
   - Approve All
   - Export OFX
   - Back to upload
4. Transactions table with columns:
   - ✓ (approve checkbox)
   - ✗ (exclude checkbox)
   - Date, Type (badge), Description, Payee, Amount, Balance, Status
5. Summary section at bottom:
   - Total debits, credits, opening/closing balance
6. JavaScript functionality:
   - Update transaction via AJAX when checkbox changes
   - Approve all button
   - Export OFX button with file download
   - Loading overlay during operations

Styling:
- Clean table design
- Color-coded amounts (red for debits, green for credits)
- Badges for transaction types and status
- Responsive layout
- Professional typography

Template should receive: request, session_id, statement, errors, warnings
Use Jinja2 templating with loops and conditionals.
```

### 4.4 - Test Web Application Locally

**Testing Prompt:**
```
Help me test the FastAPI application locally:

1. Create a test script test_webapp.py that:
   - Starts uvicorn server in background
   - Uses httpx to test endpoints
   - Tests file upload with sample PDF
   - Tests review page access
   - Tests transaction update
   - Tests OFX export
   - Validates downloaded OFX file

2. Manual testing checklist:
   - Start server: python app/main.py
   - Open http://localhost:8000
   - Upload a PDF statement
   - Verify all transactions shown in table
   - Click approve checkboxes
   - Click "Approve All"
   - Click "Export OFX"
   - Verify file downloads
   - Check that PDF is deleted from temp directory

3. Create a debugging guide for common issues:
   - Port already in use
   - File upload errors
   - Template rendering errors
   - Session not found errors

Provide curl commands to test each endpoint.
```

**✅ Checkpoint**:
```bash
# Terminal 1
python app/main.py

# Terminal 2
pytest tests/test_webapp.py -v

# Browser
http://localhost:8000 -> Upload PDF -> Review -> Export -> Import to Actual Budget
```

**Critical Test**: Import the same OFX file twice into Actual Budget - should NOT create duplicates!

---

## 🧪 PHASE 5: Integration Testing & Validation

**Goal**: Comprehensive testing before containerization.

### 5.1 - Create End-to-End Test Suite

**Prompt for Copilot/Claude:**
```
Create tests/test_e2e.py for end-to-end testing.

Test scenarios:
1. Complete workflow:
   - Upload Up Bank PDF
   - Parse all transactions
   - Review and approve all
   - Export OFX
   - Validate OFX format
   - Verify file cleanup

2. Edge cases:
   - Empty PDF
   - Scanned PDF (should fail gracefully with message)
   - Malformed PDF
   - Very large PDF (>10MB)
   - Wrong file type (.txt, .jpg)

3. Data validation:
   - All transactions have FITID
   - All amounts are Decimal with 2 decimal places
   - All dates are valid
   - Balance calculations match

4. OFX validation:
   - Parse generated OFX file
   - Verify structure matches specification
   - Check all required fields present
   - Validate CURDEF=AUD
   - Verify signed amounts

Use pytest fixtures for test data and cleanup.
Include parametrized tests for different scenarios.
```

### 5.2 - Create Test Data Generator

**Prompt for Copilot/Claude:**
```
Create tests/generate_test_data.py to create mock PDF statements for testing.

Requirements:
1. Function create_mock_up_bank_pdf(output_path, num_transactions=10):
   - Generate realistic transaction data
   - Create PDF with text (not scanned)
   - Follow Up Bank format exactly
   - Include opening/closing balance
   - Random dates within statement period
   - Mix of debits and credits
   
2. Use reportlab library to create PDF with text
3. Generate transactions with realistic:
   - Dates (sorted chronologically)
   - Merchant names (use common Australian retailers)
   - Amounts ($5 to $500 range)
   - Running balances

4. Create set of test PDFs:
   - Simple: 5 transactions
   - Medium: 20 transactions
   - Large: 100 transactions
   - Edge: Same-day duplicates, zero amounts

Save to tests/sample_statements/
```

### 5.3 - Validate Against Actual Budget

**Validation Prompt:**
```
Create a validation checklist for testing with Actual Budget:

1. OFX Import Test:
   - Generate OFX from test PDF
   - Import into Actual Budget test account
   - Verify all transactions appear
   - Check amounts are correct
   - Verify dates are correct
   - Confirm descriptions are readable

2. Duplicate Prevention Test:
   - Import same OFX file again
   - Confirm NO duplicates created
   - Actual should match by FITID first, then date/amount/payee

3. Edge Cases:
   - Import with some transactions already manually entered
   - Import partial statement (date range overlap)
   - Import multiple accounts

4. Create tests/actual_budget_validation.md documenting:
   - How to set up test account in Actual
   - Step-by-step import procedure
   - What to check after import
   - How to verify duplicate prevention
   - Screenshots of expected results

Provide a script to generate multiple test OFX files for validation.
```

**✅ Checkpoint**:
```bash
pytest tests/test_e2e.py -v
python tests/generate_test_data.py  # Creates test PDFs
python app/main.py  # Upload test PDFs and verify
```

**Manual validation**: Import ALL generated OFX files into Actual Budget. Verify:
1. All transactions appear correctly
2. Re-importing doesn't create duplicates
3. Balances are correct
4. No errors or warnings

---

## 🐳 PHASE 6: Docker Containerization

**Goal**: Create production-ready Docker images.

### 6.1 - Create Dockerfile

**Prompt for Copilot/Claude:**
```
Create a production-ready Dockerfile for the PDF-to-OFX converter.

Requirements:
1. Base image: python:3.11-slim
2. Install system dependencies:
   - tesseract-ocr (for OCR support)
   - tesseract-ocr-eng (English language pack)
   - poppler-utils (for pdf2image)
   - curl (for health checks)
3. Create non-root user 'appuser'
4. Set working directory /app
5. Copy requirements.txt and install Python packages
6. Copy application code (app/, config/)
7. Create necessary directories (data/)
8. Set ownership to appuser
9. Switch to non-root user
10. Expose port 8000
11. Add HEALTHCHECK using curl to /health endpoint
12. CMD: uvicorn with 2 workers

Optimization:
- Layer caching: Install deps before copying code
- Minimize image size: Clean apt cache
- Security: Run as non-root
- Multi-stage build if needed

Add .dockerignore file to exclude:
- venv/, __pycache__, *.pyc
- tests/, .git/
- *.md files
- sample_statements/
```

### 6.2 - Create docker-compose.yml

**Prompt for Copilot/Claude:**
```
Create docker-compose.yml for local development and production deployment.

Services:
1. pdf-to-ofx (main application):
   - Build from Dockerfile
   - Port mapping: 8000:8000
   - Volume mounts:
     - ./config:/app/config:ro (read-only configs)
     - ./data:/app/data (import history database)
   - Environment variables:
     - TZ=Australia/Melbourne
     - APP_ENV=production
     - LOG_LEVEL=INFO
     - MAX_UPLOAD_SIZE=10485760  # 10MB
     - SESSION_TIMEOUT=3600  # 1 hour
   - Resource limits:
     - CPUs: 1
     - Memory: 1GB
     - Reservations: 0.5 CPU, 512MB
   - Health check configuration
   - Restart policy: unless-stopped
   - Security options: no-new-privileges

2. nginx (optional, commented out):
   - Reverse proxy with HTTPS
   - Port mapping: 80:80, 443:443
   - Volume mounts for config and certs
   - Depends on pdf-to-ofx

3. redis (optional, commented out):
   - For session storage in production
   - Persistent volume

Add networks configuration.
Include helpful comments for production setup.
```

### 6.3 - Test Docker Build & Run

**Testing Prompt:**
```
Create a Docker testing guide docs/docker-testing.md

Include:
1. Build commands:
   - docker build -t pdf-to-ofx:latest .
   - Check image size: docker images pdf-to-ofx
   - Verify no security issues: docker scan pdf-to-ofx

2. Run commands:
   - docker-compose up -d
   - Check logs: docker-compose logs -f pdf-to-ofx
   - Check health: docker-compose ps

3. Testing inside container:
   - docker exec -it pdf-to-ofx bash
   - Test Python: python --version
   - Test Tesseract: tesseract --version
   - Test app import: python -c "from app.main import app"

4. End-to-end test with Docker:
   - Access http://localhost:8000
   - Upload PDF through web UI
   - Export OFX
   - Verify file cleanup

5. Production deployment:
   - Environment variables to set
   - Volume persistence
   - HTTPS setup with nginx
   - Backup strategies
   - Monitoring and logging

6. Troubleshooting:
   - Container won't start
   - Permission errors
   - Out of memory errors
   - Network connectivity issues

Provide Docker Compose commands for:
- Start: docker-compose up -d
- Stop: docker-compose down
- Rebuild: docker-compose up -d --build
- View logs: docker-compose logs -f
- Shell access: docker exec -it container_name bash
```

**✅ Checkpoint**:
```bash
# Build and start
docker-compose build
docker-compose up -d

# Check health
docker-compose ps
docker-compose logs pdf-to-ofx

# Test in browser
http://localhost:8000

# Full workflow test
# Upload PDF -> Review -> Export OFX -> Import to Actual Budget

# Stop
docker-compose down
```

---

## 📦 PHASE 7: Production Deployment & Documentation

**Goal**: Prepare for production use with security and documentation.

### 7.1 - Create Production Configuration

**Prompt for Copilot/Claude:**
```
Create production deployment configuration files:

1. .env.example:
   - List all environment variables needed
   - Provide example values
   - Add security warnings for secrets
   - Include comments explaining each variable

2. config/production.yaml:
   - Application settings
   - Logging configuration
   - Security settings
   - Rate limiting
   - File size limits

3. nginx.conf (for HTTPS):
   - Reverse proxy to FastAPI
   - SSL/TLS configuration
   - Security headers (HSTS, CSP, X-Frame-Options)
   - Rate limiting
   - Gzip compression
   - Static file serving

4. docs/production-deployment.md:
   - Prerequisites (server, domain, SSL cert)
   - Step-by-step deployment guide
   - Environment variable setup
   - SSL certificate installation (Let's Encrypt)
   - Firewall configuration
   - Backup procedures
   - Monitoring setup
   - Update procedures

Include security best practices:
- Use strong secrets
- Regular updates
- Access control (VPN/firewall)
- Audit logging
- Data retention policies
```

### 7.2 - Create Comprehensive Documentation

**Prompt for Copilot/Claude:**
```
Create final documentation set:

1. README.md:
   - Project overview with badges
   - Features list
   - Quick start (5-minute setup)
   - Detailed installation
   - Usage examples with screenshots
   - Configuration guide
   - Supported banks list
   - Contributing guidelines
   - License
   - FAQ

2. docs/ARCHITECTURE.md:
   - System architecture diagram
   - Data flow diagrams
   - Component descriptions
   - Design decisions and rationale
   - Technology choices explained
   - Scalability considerations

3. docs/API.md:
   - OpenAPI/Swagger documentation
   - All endpoints documented
   - Request/response examples
   - Error codes and handling
   - Authentication (if added)

4. docs/ADDING_BANKS.md:
   - Tutorial for adding new bank support
   - Template file structure
   - Parser implementation guide
   - Testing new banks
   - Example: Step-by-step for Commonwealth Bank

5. docs/TROUBLESHOOTING.md:
   - Common issues and solutions
   - Debug mode instructions
   - Log analysis
   - Performance optimization
   - Contact information

6. docs/SECURITY.md:
   - Security model
   - Data handling
   - Privacy considerations
   - Recommended deployment practices
   - Vulnerability reporting

Use clear headings, code blocks, and examples throughout.
Include table of contents in each doc.
```

### 7.3 - Create Maintenance Scripts

**Prompt for Copilot/Claude:**
```
Create maintenance and utility scripts:

1. scripts/backup.sh:
   - Backup config files
   - Backup import history database
   - Compress and timestamp
   - Optional upload to cloud storage

2. scripts/update.sh:
   - Pull latest code from git
   - Rebuild Docker image
   - Restart containers with zero downtime
   - Run database migrations if needed

3. scripts/health-check.sh:
   - Check if application is responding
   - Check disk space
   - Check memory usage
   - Send alerts if issues detected

4. scripts/cleanup.sh:
   - Remove old session data
   - Clean up orphaned temp files
   - Rotate logs
   - Database cleanup (old import history)

5. scripts/test-ofx.py:
   - Validate OFX file format
   - Check all required fields
   - Verify FITID uniqueness
   - Test import into Actual Budget (automated)

Make all scripts executable with proper error handling.
Include usage instructions in comments.
```

**✅ Final Checkpoint**:

```bash
# Complete workflow from fresh checkout
git clone <repo>
cd pdf-to-ofx

# Local development
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app/main.py
# Test at http://localhost:8000

# Run all tests
pytest tests/ -v --cov=app

# Docker deployment
docker-compose build
docker-compose up -d
# Test at http://localhost:8000

# Production deployment
# Follow docs/production-deployment.md

# Validate with Actual Budget
# Import multiple OFX files
# Verify no duplicates
# Test edge cases
```

---

## 🎯 Summary Workflow for AI Pair Programming

### With GitHub Copilot in VSCode:

1. **Start each file** with a detailed comment block describing what you need
2. **Tab through suggestions** - Copilot will generate code based on context
3. **Refine with comments** - Add "TODO:" or "FIXME:" for specific changes
4. **Use inline chat** - Ctrl+I to ask for modifications

Example workflow:
```python
# Create a function to parse Australian bank statement PDF
# Should extract: date, description, amount, balance
# Handle Up Bank format: "Wednesday, 21st Jan" followed by transaction details
# Return list of Transaction objects
```
Then Tab → Copilot generates the function → Refine as needed.

### With Claude 4.5 in Chat:

1. **Copy-paste prompts** from each phase above
2. **Review generated code** - don't blindly copy
3. **Ask for explanations** - "Why did you choose this approach?"
4. **Request modifications** - "Make this more efficient" or "Add error handling"
5. **Iterate** - Keep refining until it's exactly right

### Recommended Workflow:

```
Phase 1-3 (Core Logic):
→ Use Claude 4.5 for initial code generation (paste prompts)
→ Use Copilot for refinement and completion in VSCode
→ Test locally after each component

Phase 4-5 (Web App & Testing):
→ Use Claude for complex logic (parsers, validators)
→ Use Copilot for repetitive code (routes, templates)
→ Test continuously in browser

Phase 6-7 (Docker & Production):
→ Use Claude for configuration files (Dockerfile, nginx)
→ Use Copilot for scripts and documentation
→ Test deployment thoroughly
```

---

## ✅ Quality Gates (Don't Skip!)

### After Each Phase:

**Phase 1**: 
```bash
pytest tests/test_models.py -v
python -c "from app.models import Transaction; print('✅ Models OK')"
```

**Phase 2**:
```bash
pytest tests/test_fitid_generator.py tests/test_ofx_generator.py -v
python app/services/ofx_generator.py  # Inspect output OFX file
```

**Phase 3**:
```bash
python app/services/up_bank_parser.py  # Should parse real PDF
# Manually verify: correct transaction count, amounts, dates
```

**Phase 4**:
```bash
python app/main.py  # Start server
# Open browser, test complete workflow
# Check temp files are deleted after export
```

**Phase 5**:
```bash
pytest tests/ -v --cov=app --cov-report=html
# Open htmlcov/index.html - aim for >80% coverage
```

**Phase 6**:
```bash
docker-compose up -d
docker-compose logs -f
# Test at http://localhost:8000
# Import OFX into Actual Budget
```

**Phase 7**:
```bash
# Follow production deployment guide
# Test in production-like environment
# Verify security settings
# Run load tests if needed
```

---

## 🚨 Common Pitfalls to Avoid

1. **Don't skip testing** - Test after each component, not at the end
2. **Don't assume Copilot is correct** - Always review generated code
3. **Don't ignore type hints** - Use mypy: `mypy app/ --strict`
4. **Don't hardcode values** - Use environment variables and config files
5. **Don't forget error handling** - Every external call needs try/except
6. **Don't neglect logging** - Add logging.info() at key points
7. **Don't skip documentation** - Document as you code, not after

---

## 📞 Getting Help from AI

### When to use GitHub Copilot:
- Autocomplete repetitive code
- Generate boilerplate (tests, models)
- Refactor existing code
- Suggest function signatures
- Inline quick fixes

### When to use Claude 4.5:
- Design architectural decisions
- Debug complex issues
- Write comprehensive tests
- Create documentation
- Explain complex code
- Generate entire new components
- Code reviews and optimization

### Effective Prompting Tips:

**Bad Prompt:**
"Make a PDF parser"

**Good Prompt:**
"Create a Python class PDFTextExtractor that uses pdfplumber to extract transaction tables from Australian bank statement PDFs. Should detect if PDF is text-based (>100 chars/page), extract tables with configurable column detection, and provide utility methods to parse amounts ($42.00, -$42.00, ($42.00)) and Australian date formats (21st Jan 2026, 21/01/2026). Include comprehensive error handling and logging."

### Debugging with AI:

Instead of: "This doesn't work"

Try: "I'm getting a KeyError when parsing transaction date. Here's the code: [paste code]. Here's the error: [paste traceback]. The input data looks like: [paste sample]. I think it's related to date format parsing. Can you help debug?"

---

## 🎓 Learning & Iteration

### Code Review Checklist (Ask Claude to Review):

```
Review this code for:
1. Type safety - are all type hints correct?
2. Error handling - are exceptions caught appropriately?
3. Performance - any obvious bottlenecks?
4. Security - any input validation missing?
5. Readability - clear variable names and comments?
6. Testability - easy to unit test?
7. Best practices - following Python/FastAPI conventions?

[paste your code]
```

### Continuous Improvement:

After completing each phase:
1. Ask Claude: "How could I improve this code?"
2. Run linters: `ruff check app/` and `black app/`
3. Check security: `bandit -r app/`
4. Measure coverage: `pytest --cov=app --cov-report=term-missing`
5. Profile performance: Use cProfile for slow operations

---

## 🎉 Final Delivery Checklist

Before considering the project "done":

- [ ] All tests passing (pytest shows 100% passed)
- [ ] Code coverage >80% (check htmlcov/index.html)
- [ ] Type checking passes (mypy --strict app/)
- [ ] Linting passes (ruff, black, isort)
- [ ] Security scan clean (bandit -r app/)
- [ ] Documentation complete (all .md files)
- [ ] Docker builds successfully
- [ ] Docker container runs and serves requests
- [ ] Manual testing completed:
  - [ ] Upload PDF
  - [ ] Review transactions
  - [ ] Export OFX
  - [ ] Import to Actual Budget
  - [ ] Re-import same OFX (verify no duplicates)
  - [ ] Test with 3+ different PDFs
- [ ] Production deployment tested (if deploying)
- [ ] README has installation and usage examples
- [ ] GitHub repo is clean (no secrets, organized structure)

---

## 🔄 Iteration Strategy

**If something doesn't work:**

1. **Reproduce the issue** - Get exact error message
2. **Isolate the problem** - Which component is failing?
3. **Gather context** - What's the input data?
4. **Ask AI specifically** - Paste error + code + input
5. **Test the fix** - Create a test case first
6. **Document the solution** - Add to troubleshooting guide

**Example debugging prompt for Claude:**

```
I'm getting this error when parsing an Up Bank PDF:

Error: KeyError: 'date_posted'
Traceback: [full traceback]

Here's my parser code: [paste code]
Here's a sample of the PDF text: [paste first 100 lines]
Here's what the transactions list looks like: [paste debug output]

Expected: date_posted should be 2026-01-21
Actual: KeyError raised

Can you help identify why date_posted is missing from the transaction dictionary?
```

---

This guide should give you a complete roadmap for building the project phase-by-phase with AI assistance. Remember: **test continuously, commit often, and don't move to the next phase until the current one is solid!**

Good luck! 🚀
