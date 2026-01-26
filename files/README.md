# PDF to OFX Converter for Actual Budget

A self-hosted web application that converts Australian bank PDF statements into OFX format for importing into [Actual Budget](https://actualbudget.com/).

## ✨ Features

- ✅ **Text-based PDF extraction** using pdfplumber
- 🔄 **OCR support** for scanned PDFs (via Tesseract)
- 🏦 **Multi-bank support** with template-based parsing
- ✏️ **Human verification** step before export
- 🔒 **Privacy-focused** - PDFs deleted immediately after export
- 🎯 **Stable FITID generation** - prevents duplicates in Actual Budget
- 🌏 **Australian banks** (AUD currency)
- 🚀 **Fast and lightweight** FastAPI backend

## 🏗️ Architecture

```
Upload PDF → Extract Transactions → Review & Edit → Export OFX → Import to Actual
     ↓              ↓                    ↓              ↓
  Text/OCR    Template Parser    Human Approval    FITID Gen    (File deleted)
```

## 📋 Prerequisites

### System Requirements
- Python 3.10 or higher
- Tesseract OCR (for scanned PDFs)
- Linux/macOS (recommended) or Windows with WSL

### Install Tesseract

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng
```

**macOS:**
```bash
brew install tesseract
```

**Verify installation:**
```bash
tesseract --version
```

## 🚀 Quick Start

### 1. Clone or Download

```bash
git clone <repository-url>
cd pdf-to-ofx
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
# Development mode (auto-reload)
python app/main.py

# Or use uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Open in Browser

Navigate to: http://localhost:8000

## 📖 Usage Guide

### Step 1: Upload Statement

1. Go to http://localhost:8000
2. Enter an **Account Name** (e.g., `up_spending`, `commbank_checking`)
3. Select your **Bank** from the dropdown
4. Upload your **PDF statement**
5. Click **Upload & Extract Transactions**

### Step 2: Review Transactions

1. Review all extracted transactions in the table
2. Check the ✓ column to approve individual transactions
3. Check the ✗ column to exclude transactions
4. Use **Approve All** button to approve everything at once
5. Verify the summary balances match your statement

### Step 3: Export OFX

1. Click **Export OFX** button
2. Save the downloaded `.ofx` file
3. Your uploaded PDF is automatically deleted

### Step 4: Import to Actual Budget

1. Open Actual Budget
2. Go to your target account
3. Click **Import** button
4. Select the downloaded OFX file
5. Review and confirm the import

**Note:** Re-importing the same OFX file won't create duplicates thanks to stable FITID values!

## 🏦 Supported Banks

### Currently Supported
- ✅ **Up Bank** (Bendigo and Adelaide Bank)

### Coming Soon
- 🔄 Commonwealth Bank
- 🔄 ANZ
- 🔄 Westpac
- 🔄 NAB

**Want to add your bank?** See [Adding New Banks](#adding-new-banks) below.

## 🔧 Configuration

### Account Mapping

Create `config/accounts.yaml` (optional):

```yaml
accounts:
  up_spending:
    bank: up
    account_id: "spending"
    account_type: CHECKING
  
  commbank_savings:
    bank: commbank
    account_id: "12345678"
    account_type: SAVINGS
```

### Bank Templates

Bank templates are in `config/templates/`. Example structure:

```yaml
# config/templates/up_bank.yaml
bank:
  name: "Up Bank"
  identifier: "up"
  default_bank_id: "000000"

detection:
  keywords:
    - "Up is a brand of Bendigo"
    - "up.com.au"

parsing:
  date_formats:
    - "%A, %d %b"
    - "%d %b"
  
  memo_cleanup:
    - pattern: "\\s+Round Up$"
      replacement: ""
```

## 🧪 Testing

### Test the OFX Generator

```bash
cd /home/claude
python app/services/ofx_generator.py
```

This will generate a sample OFX file at `/tmp/test_statement.ofx`.

### Test the Text Extractor

```bash
python app/services/text_extractor.py /path/to/your/statement.pdf
```

### Test the Up Bank Parser

```bash
python app/services/up_bank_parser.py
```

### Run Unit Tests

```bash
pytest tests/
```

## 🏗️ Project Structure

```
pdf-to-ofx/
├── app/
│   ├── main.py                  # FastAPI application
│   ├── models.py                # Pydantic data models
│   ├── services/
│   │   ├── text_extractor.py   # PDF text extraction
│   │   ├── ocr_extractor.py    # OCR for scanned PDFs
│   │   ├── up_bank_parser.py   # Bank-specific parser
│   │   ├── fitid_generator.py  # Stable transaction IDs
│   │   └── ofx_generator.py    # OFX v1 SGML generation
│   └── templates/
│       ├── upload.html          # Upload page
│       └── review.html          # Review page
├── config/
│   └── templates/               # Bank parsing templates
├── requirements.txt
└── README.md
```

## 🔐 Security & Privacy

- ✅ PDFs are stored in temporary directories only
- ✅ PDFs are **deleted immediately** after OFX export
- ✅ No financial data is persisted to disk
- ✅ Session data cleared after export
- ✅ File type validation (PDF only)
- ✅ File size limits enforced

**For production:**
- Use HTTPS (reverse proxy with nginx/caddy)
- Add authentication (basic auth or OAuth)
- Run behind VPN/firewall
- Use environment variables for secrets

## 📝 Adding New Banks

To add support for a new bank:

### 1. Analyze the PDF

- Check if text-based or scanned
- Identify transaction table columns
- Note date format, amount format
- Find running balance column (if any)
- Look for statement period indicators

### 2. Create Template YAML

Create `config/templates/yourbank.yaml`:

```yaml
bank:
  name: "Your Bank"
  identifier: "yourbank"
  default_bank_id: "XXXXXX"  # BSB or institution code

detection:
  keywords:
    - "Unique text from your bank"
    - "yourbank.com.au"

extraction:
  text_mode:
    enabled: true
  
parsing:
  date_formats:
    - "%d/%m/%Y"
  
  amount_parsing:
    debit_column: true  # or false if single signed column
    credit_column: true
```

### 3. Create Parser Class

Create `app/services/yourbank_parser.py`:

```python
from app.services.text_extractor import PDFTextExtractor
from app.models import Transaction, Statement

class YourBankParser:
    BANK_NAME = "Your Bank"
    BANK_ID = "XXXXXX"
    
    def parse_statement(self, account_key: str) -> Statement:
        # Implement parsing logic
        pass
```

### 4. Register in Main App

Update `app/main.py`:

```python
elif bank_template == "yourbank":
    parser = YourBankParser(pdf_path)
    statement = parser.parse_statement(account_key)
```

### 5. Test Thoroughly

```bash
python app/services/yourbank_parser.py
```

Test with multiple statements to ensure:
- All transactions extracted
- Dates parsed correctly
- Amounts signed correctly (negative for debits)
- Balance calculations match

## 🐛 Troubleshooting

### "PDF appears to be scanned"

**Solution:** Install Tesseract and implement OCR extractor for your bank.

### "Failed to extract transactions"

**Possible causes:**
1. Bank template doesn't match PDF format
2. Date format not recognized
3. Table structure changed

**Solution:** 
- Check PDF manually
- Update template configuration
- Add debug logging to parser

### "Balance doesn't match"

**Causes:**
- Missing transactions
- Incorrect amount parsing
- Wrong sign on amounts

**Solution:**
- Check all transactions are extracted
- Verify debits are negative, credits positive
- Check for fees/charges in separate sections

### "Duplicates in Actual Budget"

**Cause:** FITID not stable across imports

**Solution:**
- Ensure FITID generation uses all key fields
- Include balance in hash if available
- Check for reference numbers in statement

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY config/ config/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  pdf-to-ofx:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
    environment:
      - TZ=Australia/Melbourne
    restart: unless-stopped
```

### Build and Run

```bash
docker-compose up -d
```

## 📊 OFX Format Details

### Structure

The generated OFX follows v1.02 SGML format:

```
OFXHEADER:100
DATA:OFXSGML
VERSION:102
...
<OFX>
  <SIGNONMSGSRSV1>...</SIGNONMSGSRSV1>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <CURDEF>AUD
        <BANKACCTFROM>
          <BANKID>063262
          <ACCTID>12345678
          <ACCTTYPE>SAVINGS
        </BANKACCTFROM>
        <BANKTRANLIST>
          <STMTTRN>
            <TRNTYPE>DEBIT
            <DTPOSTED>20260125
            <TRNAMT>-42.00
            <FITID>ABC123...
            <MEMO>Description
          </STMTTRN>
          ...
        </BANKTRANLIST>
        <LEDGERBAL>...</LEDGERBAL>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>
```

### Key Fields

- **CURDEF**: Always `AUD`
- **TRNAMT**: Negative for debits, positive for credits
- **FITID**: Stable unique ID (prevents duplicates)
- **DTPOSTED**: Date in YYYYMMDD format

## 🤝 Contributing

Contributions welcome! Especially:
- New bank parsers
- OCR improvements
- UI enhancements
- Bug fixes

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF extraction
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Actual Budget](https://actualbudget.com/) - Budgeting software
- [OFX Tools](https://github.com/csingley/ofxtools) - OFX reference

## 📞 Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review existing GitHub issues
3. Create a new issue with:
   - PDF bank/type
   - Error messages
   - Expected vs actual behavior

## 🗺️ Roadmap

- [x] MVP with Up Bank support
- [x] Web UI with transaction review
- [x] Stable FITID generation
- [ ] OCR extractor implementation
- [ ] Commonwealth Bank template
- [ ] ANZ template
- [ ] Import history tracking
- [ ] Batch processing
- [ ] API-only mode
- [ ] Mobile-responsive UI
- [ ] Docker deployment guide

---

**⚠️ Disclaimer:** This tool is for personal use only. Always verify your OFX files before importing. No warranty provided. Use at your own risk.
