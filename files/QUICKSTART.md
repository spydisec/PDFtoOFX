# 🚀 Quick Start Guide - PDF to OFX Converter

Get up and running in 5 minutes!

## Prerequisites Check

```bash
# Check Python version (need 3.10+)
python3 --version

# Check if Tesseract is installed
tesseract --version
```

If Tesseract is not installed:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

## Installation

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- FastAPI (web framework)
- pdfplumber (PDF extraction)
- pytesseract (OCR)
- Pydantic (data validation)
- And more...

### 3. Run the Application

```bash
python app/main.py
```

Or with uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Open Your Browser

Go to: **http://localhost:8000**

## First Conversion

### Test with Example PDF

If you have the Up Bank PDF example:

1. **Upload**
   - Account Name: `up_spending`
   - Bank: `Up Bank`
   - Upload the PDF

2. **Review**
   - Check extracted transactions
   - Click "Approve All"

3. **Export**
   - Click "Export OFX"
   - Save the file

4. **Import to Actual Budget**
   - Open Actual Budget
   - Go to your account
   - Click Import → Select OFX file

## Testing the Components

### Test OFX Generation

```bash
cd /home/claude
python3 example_ofx_generator.py
```

This creates `/home/claude/example_output.ofx` showing the exact format.

### Test FITID Generation

```bash
PYTHONPATH=/home/claude python3 -c "
from app.services.fitid_generator import FITIDGenerator
from decimal import Decimal

gen = FITIDGenerator()
fitid = gen.generate(
    bank_id='000000',
    account_key='test',
    date_posted='2026-01-26',
    amount=Decimal('-42.00'),
    memo='Test Transaction'
)
print(f'Generated FITID: {fitid}')
"
```

## Common Issues

### "Module not found" errors

Solution:
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Cannot connect to localhost:8000"

Solution:
```bash
# Check if app is running
ps aux | grep uvicorn

# Try a different port
uvicorn app.main:app --port 8001
```

### PDF extraction fails

Solution:
1. Check if PDF is text-based (can you copy text from it?)
2. If scanned, ensure Tesseract is installed
3. Check the logs for specific errors

## Docker Quick Start

If you prefer Docker:

```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

Access at: http://localhost:8000

## Next Steps

1. ✅ Convert your first statement
2. 📖 Read the full [README.md](README.md)
3. 🏦 Add templates for your banks
4. 🔒 Set up HTTPS for production
5. 🧪 Run tests: `pytest tests/`

## Production Deployment

For production use:

1. **Use HTTPS** - Set up nginx reverse proxy
2. **Add Authentication** - Basic auth or OAuth
3. **Run Behind Firewall** - VPN access only
4. **Use Environment Variables** - For sensitive config
5. **Enable Logging** - Monitor for errors
6. **Set Resource Limits** - CPU/memory constraints

See [README.md](README.md) for detailed production setup.

## Getting Help

- 📖 Read the [full documentation](README.md)
- 🐛 Check [troubleshooting section](README.md#troubleshooting)
- 💬 Create an issue on GitHub
- 🏦 Share bank templates you create!

---

**Ready to convert?** Open http://localhost:8000 and start uploading! 🎉
