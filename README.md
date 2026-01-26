# ANZ Plus to OFX Converter

Convert ANZ Plus bank statement PDFs to OFX format for seamless import into Actual Budget and other personal finance applications.

[![Tests](https://img.shields.io/badge/tests-6%2F6%20passing-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![Docker](https://img.shields.io/badge/docker-multi--arch-blue)](https://hub.docker.com/r/spydisec/anzplus-ofx-converter)
[![License](https://img.shields.io/badge/license-MIT-blue)]()

## ✨ Features

- **🎨 Modern Web Interface** - Drag-and-drop PDF upload with instant conversion
- **📝 Multi-line Descriptions** - Captures complete transaction details including merchant, location, and reference numbers
- **🎯 Smart Truncation** - Preserves merchant names in OFX NAME field by removing common prefixes
- **💯 Accurate Detection** - Uses balance change analysis for reliable credit/debit identification
- **🔐 Collision-free IDs** - Sequential FITID strategy ensures unique transaction IDs for duplicate prevention
- **📊 Complete History** - Converts all transactions without filtering to maintain accurate balances
- **⚡ OFX v2.20 XML** - Modern format compatible with Actual Budget and other finance apps

## 🚀 Quick Start

### 🐳 Option 1: Docker (Recommended)

**Official multi-architecture image** - automatically built and published via GitHub Actions:

```bash
# Pull and run from Docker Hub (no installation required!)
docker pull spydisec/anzplus-ofx-converter:latest
docker run -d -p 8000:8000 spydisec/anzplus-ofx-converter:latest

# Open your browser to http://localhost:8000
```

**Why Docker?**
- ✅ No Python installation required
- ✅ Works on Windows, Mac, Linux
- ✅ Multi-architecture support (amd64, arm64/Apple Silicon)
- ✅ Production-ready configuration
- ✅ Automatic health checks
- ✅ Simple version pinning

**Version Pinning (Production):**
```bash
# Pin to specific version (recommended for stability)
docker run -d -p 8000:8000 spydisec/anzplus-ofx-converter:1.0.0

# Or always use latest
docker run -d -p 8000:8000 spydisec/anzplus-ofx-converter:latest
```

**Custom Configuration:**
```bash
docker run -d -p 8000:8000 \
  -e WORKERS=8 \
  -e LOG_LEVEL=debug \
  -e ENVIRONMENT=production \
  spydisec/anzplus-ofx-converter:latest
```

**Docker Compose:**
```yaml
version: '3.8'
services:
  anzplus-ofx-converter:
    image: spydisec/anzplus-ofx-converter:latest
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - WORKERS=4
      - LOG_LEVEL=info
    restart: unless-stopped
```

**Build Locally (Optional):**

Most users should use the official image. For development:

```powershell
# Windows
.\docker\build-local.ps1

# Linux/Mac
docker build -f docker/Dockerfile -t anzplus-ofx:local .
```

**📚 Full Docker documentation: [docker/README.md](docker/README.md)**

### 🐍 Option 2: Python Installation

For local development or customization:

#### Installation

```bash
# Clone the repository
git clone https://github.com/spydisec/PDFtoOFX.git
cd PDFtoOFX

# Create and activate virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\Activate.ps1  # On Windows

# Install dependencies
pip install -r requirements.txt
```

**📚 For detailed installation instructions including Linux self-hosting, systemd service setup, and Nginx configuration, see [INSTALLATION.md](INSTALLATION.md)**

#### Web Interface

#### Web Interface

Launch the elegant web app with drag-and-drop file upload:

```bash
python run_web.py
```

Then open **http://localhost:8000** in your browser.

**Web Interface Features:**
- 🎨 Minimalistic design with Tailwind CSS
- 📤 Drag-and-drop PDF upload
- ⚡ Real-time conversion progress
- 📥 One-click OFX download
- 🔒 Secure (files processed in memory, auto-deleted after download)
- 📱 Fully mobile responsive

#### Command Line Interface

```bash
python convert_pdf.py input.pdf output.ofx
```

**Example:**
```bash
python convert_pdf.py statement.pdf statement.ofx
```

**Output:**
```
Converting: statement.pdf
Output to: statement.ofx

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
  ✓ Saved to statement.ofx

✅ Conversion complete!
```

## 📥 Import to Actual Budget

1. Open Actual Budget
2. Navigate to your account
3. Click **Import** → **Select File**
4. Choose your `.ofx` file
5. Review and approve transactions

**Verify Duplicate Detection:**  
Re-import the same OFX file to confirm all transactions are detected as duplicates, validating the FITID strategy.

## 🏦 Supported Bank

This converter is **specifically designed for ANZ Plus** digital PDF statements.

**✅ Supported:**
- ANZ Plus digital PDF statements
- Transaction format: Date, Description, Credit, Debit, Balance columns
- Multi-line transaction details

**❌ Not Supported:**
- Other ANZ products (ANZ Classic, ANZ Access, etc.) - different formats
- Scanned/image PDFs - no OCR functionality
- Other banks - requires bank-specific parsers

## 📝 Transaction Example

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
- **NAME:** `MYKI PAYMENTS MELBOURNE` (merchant visible, smart truncation)
- **MEMO:** Full description with all details
- **Type:** Correctly identified as DEBIT using balance analysis
- **FITID:** `ANZ_20260122_0001` (unique, collision-free)

## 📂 Project Structure

```
PDFtoOFX/
├── README.md                    # This file
├── ARCHITECTURE.md              # Technical documentation
├── LICENSE                      # MIT license
├── pyproject.toml              # Package configuration
├── requirements.txt            # Dependencies
├── requirements-dev.txt        # Development dependencies
│
├── run_web.py                  # Web app launcher
├── convert_pdf.py              # CLI tool
│
├── app/                        # Application code
│   ├── models.py               # Pydantic data models
│   ├── services/               # Core business logic
│   │   ├── anz_plus_parser.py  # ANZ Plus PDF parser
│   │   ├── fitid_generator.py  # Unique ID generation
│   │   ├── ofx_generator.py    # OFX XML generation
│   │   └── pdf_extractor.py    # PDF text extraction
│   └── web/                    # Web application
│       ├── main.py             # FastAPI app
│       ├── routes.py           # API endpoints
│       └── templates/          # HTML templates
│
└── tests/                      # Test suite
    └── test_converter.py       # Unit & integration tests
```

## 🛠️ Requirements

- **Python:** 3.11 or higher
- **Dependencies:**
  - `ofxtools>=0.9.6` - OFX v2.20 XML generation
  - `pdfplumber>=0.11.9` - PDF text extraction
  - `pydantic>=2.12.5` - Data validation
  - `python-dateutil` - Date parsing
  - `fastapi>=0.109.0` - Web framework
  - `uvicorn[standard]>=0.27.0` - ASGI server
  - `jinja2>=3.1.3` - Template rendering
  - `python-multipart>=0.0.6` - File uploads
  - `aiofiles>=23.2.1` - Async file operations

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=app --cov-report=html
```

**Test Results:**
```
✅ 6/6 tests passing
✅ 91% code coverage
✅ FITID collision detection verified
✅ Multi-line description capture validated
✅ Smart truncation tested
✅ End-to-end conversion verified
```

## 🔧 Development

### Setup Development Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt
```

### Code Style

- Follow **PEP 8** guidelines
- Use **type hints** for all functions
- Write **docstrings** for public APIs
- Maximum line length: **100 characters**

### Running the Web App in Development

```bash
# Auto-reload on code changes
python run_web.py

# Or use uvicorn directly
uvicorn app.web.main:app --reload --port 8000
```

### Pre-commit Checks

```bash
# Format code
black app/ tests/

# Run linter
flake8 app/ tests/

# Type checking
mypy app/

# Run tests
pytest tests/ -v
```

## 🤝 Contributing

Contributions are welcome! Here's how:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes
4. **Add** tests for new functionality
5. **Ensure** all tests pass (`pytest tests/ -v`)
6. **Commit** your changes (`git commit -m 'Add amazing feature'`)
7. **Push** to the branch (`git push origin feature/amazing-feature`)
8. **Open** a Pull Request

### Contribution Guidelines

- Write tests for new features
- Maintain or improve code coverage (currently 91%)
- Follow existing code style and patterns
- Update documentation as needed

## 📋 How It Works

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical documentation.

**High-level flow:**
1. **Extract** text from PDF using pdfplumber
2. **Parse** transactions with regex patterns (supports multi-line descriptions)
3. **Truncate** smartly (remove common prefixes, preserve merchant names)
4. **Detect** credit/debit using balance change analysis
5. **Generate** unique FITIDs using sequential counter
6. **Create** OFX v2.20 XML using ofxtools library

## ⚠️ Known Limitations

- **Single Bank:** Currently only supports ANZ Plus PDF format
- **Digital Only:** Does not support scanned/image PDFs (no OCR)
- **Date Handling:** Uses current year if not found in PDF
- **Manual Categorization:** Transactions import uncategorized

## 🚀 Deployment Options

### 🐳 Docker (Recommended for Production)

**Pull from Docker Hub:**
```bash
docker pull spydisec/anzplus-ofx-converter:latest
docker run -d -p 8000:8000 --restart unless-stopped spydisec/anzplus-ofx-converter:latest
```

**Using Docker Compose:**
```yaml
version: '3.8'
services:
  anzplus-ofx:
    image: spydisec/anzplus-ofx-converter:latest
    ports:
      - "8000:8000"
    environment:
      - WORKERS=4
      - LOG_LEVEL=info
    restart: unless-stopped
```

**Multi-Architecture Support:**
- Automatically pulls correct image for your platform
- Supports: linux/amd64 (Intel/AMD), linux/arm64 (Apple Silicon, ARM)

**📚 Complete Docker guide:** [docker/README.md](docker/README.md)

### Local Development
```bash
python run_web.py
```

### Cloud Platforms

**Container-based (Docker):**
- **Render.com:** Free tier available, auto-deploy from GitHub
- **Railway.app:** $5/month, easy Docker deployment
- **Fly.io:** Pay-as-you-go, multi-region, global edge
- **AWS ECS/Fargate:** Enterprise-grade container orchestration
- **Google Cloud Run:** Serverless containers, auto-scaling

**Traditional hosting:**
- Self-hosted VPS with systemd service (see [INSTALLATION.md](INSTALLATION.md))

## 🐛 Troubleshooting

### Web app won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Use different port
uvicorn app.web.main:app --port 3000
```

### PDF conversion fails
- Ensure PDF is from ANZ Plus (not ANZ Classic/Access)
- Verify PDF is not scanned/image-based
- Check PDF is not password-protected

### Balance mismatch in Actual Budget
- All transactions are now preserved (including ROUND UP)
- Verify opening and closing balances match your PDF
- Check for any filtered transactions

## 📄 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [ofxtools](https://github.com/csingley/ofxtools) - OFX file generation
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF text extraction
- [Actual Budget](https://actualbudget.com/) - Personal finance management
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS
- [HTMX](https://htmx.org/) - Dynamic HTML interactions

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/spydisec/PDFtoOFX/issues)
- **Installation Guide:** [INSTALLATION.md](INSTALLATION.md) - Detailed setup for Linux, Docker, systemd, etc.
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md) - Technical documentation
- **Repository:** [github.com/spydisec/PDFtoOFX](https://github.com/spydisec/PDFtoOFX)

---

**Note:** This project is not affiliated with ANZ Bank. It is an independent tool created for personal finance management.

**Made with ❤️ for the Actual Budget community**
