# Development Guide

## Contributing to ANZ Plus PDF to OFX Converter

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

### Prerequisites
- Python 3.11 or higher
- Git
- Virtual environment tool (venv, virtualenv, or conda)

### Setup Steps

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/PDFtoOFX.git
   cd PDFtoOFX
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   # Install development dependencies
   pip install -r requirements-dev.txt
   
   # Or install in editable mode
   pip install -e ".[dev]"
   ```

4. **Verify Installation**
   ```bash
   # Run tests
   python -m pytest tests/ -v
   
   # Run converter
   python convert_pdf.py examples/pdfs/sample_anz_plus.pdf test.ofx
   ```

## Project Structure

```
PDFtoOFX/
├── app/
│   ├── models.py                  # Pydantic data models
│   └── services/
│       ├── anz_plus_parser.py     # ANZ Plus PDF parser
│       ├── fitid_generator.py     # FITID generation
│       ├── ofx_generator.py       # OFX XML generation
│       └── pdf_extractor.py       # PDF text extraction
├── tests/
│   └── test_converter.py          # Test suite
├── docs/                          # Documentation
├── examples/                      # Sample files
└── convert_pdf.py                 # CLI entry point
```

## Code Style

### Python Style
- Follow **PEP 8** guidelines
- Use **type hints** for function parameters and return values
- Write **docstrings** for all public functions and classes
- Maximum line length: **100 characters**

### Example
```python
def parse_transaction(
    line: str, 
    year: int = None
) -> Optional[Transaction]:
    """
    Parse a single transaction line from ANZ Plus PDF.
    
    Args:
        line: Raw transaction line from PDF
        year: Year for date parsing (default: current year)
        
    Returns:
        Transaction object or None if line doesn't match pattern
    """
    # Implementation
    pass
```

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `AnzPlusParser`)
- **Functions/Methods**: `snake_case` (e.g., `parse_transaction`)
- **Constants**: `UPPER_CASE` (e.g., `TRANSACTION_PATTERN`)
- **Private methods**: `_leading_underscore` (e.g., `_parse_date`)

## Testing

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=term-missing

# Run specific test
python -m pytest tests/test_converter.py::TestAnzPlusParser -v
```

### Writing Tests
- Use **pytest** framework
- Aim for **>85% code coverage**
- Test both **success and error cases**
- Use **descriptive test names**

### Example Test
```python
def test_parse_multi_line_transaction():
    """Test that multi-line descriptions are captured"""
    parser = AnzPlusParser(year=2026)
    text = """22 Jan VISA DEBIT PURCHASE CARD 1633 MYKI $25.00 $233.45
PAYMENTS MELBOURNE"""
    
    statement = parser.parse(text)
    assert len(statement.transactions) == 1
    assert "PAYMENTS MELBOURNE" in statement.transactions[0].description
```

### Test Coverage Requirements
- **New features**: Must include tests
- **Bug fixes**: Add test reproducing the bug
- **Minimum coverage**: 85% for new code

## Adding Features

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Implement Changes
- Write code following style guidelines
- Add tests for new functionality
- Update documentation

### 3. Run Tests
```bash
# Ensure all tests pass
python -m pytest tests/ -v

# Check coverage
python -m pytest tests/ --cov=app --cov-report=term-missing
```

### 4. Commit Changes
```bash
git add .
git commit -m "feat: add support for X"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring

### 5. Push and Create PR
```bash
git push origin feature/your-feature-name
```
Then create a Pull Request on GitHub.

## Adding Support for Other Banks

To add support for another bank:

### 1. Create Parser
Create a new parser in `app/services/`:

```python
# app/services/commbank_parser.py

class CommBankParser:
    """Parser for CommBank PDF transaction lists"""
    
    TRANSACTION_PATTERN = r'...'  # Bank-specific regex
    
    def parse(self, text: str) -> Statement:
        """Parse CommBank PDF text into Statement"""
        # Implementation
        pass
```

### 2. Add Tests
```python
# tests/test_commbank_parser.py

def test_commbank_transaction_parsing():
    parser = CommBankParser()
    # Test implementation
```

### 3. Update CLI
Add bank detection in `convert_pdf.py`:

```python
def detect_bank(text: str) -> str:
    """Detect bank from PDF text"""
    if "ANZ Plus" in text:
        return "anz_plus"
    elif "CommBank" in text:
        return "commbank"
    # ...
```

### 4. Document
- Update README.md with supported banks
- Add examples to `examples/` directory
- Update docs/QUICKSTART.md

## Debugging

### Enable Verbose Output
```python
# Add logging to parser
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test with Sample PDF
```bash
# Extract text to see what parser receives
python -c "from app.services.pdf_extractor import extract_text_from_pdf; from pathlib import Path; print(extract_text_from_pdf(Path('your.pdf')))"
```

### Validate OFX Output
```bash
# Check OFX structure
python -c "import xml.etree.ElementTree as ET; tree = ET.parse('output.ofx'); print(ET.tostring(tree.getroot(), encoding='unicode'))"
```

## Common Issues

### Issue: Tests Failing on File Paths
**Solution:** Use `Path` objects for cross-platform compatibility
```python
from pathlib import Path
pdf_path = Path("examples/pdfs/sample.pdf")
```

### Issue: OFX Not Importing
**Solution:** Validate OFX structure and required fields
- Check FITID is present and unique
- Verify DTPOSTED format
- Ensure TRNAMT is numeric

### Issue: Parser Not Finding Transactions
**Solution:** Debug regex patterns
```python
import re
pattern = r'your_pattern'
text = "sample line"
match = re.match(pattern, text)
if match:
    print(match.groups())
```

## Pull Request Process

1. **Fork** the repository
2. **Create branch** for your feature
3. **Write code** following style guidelines
4. **Add tests** with good coverage
5. **Update docs** if needed
6. **Run tests** and ensure they pass
7. **Submit PR** with clear description

### PR Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Added tests for new features
- [ ] Updated documentation
- [ ] No merge conflicts
- [ ] Descriptive PR title and description

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. Create GitHub release
6. (Optional) Publish to PyPI

## Getting Help

- **Issues**: Report bugs or request features
- **Discussions**: Ask questions or share ideas
- **Documentation**: Check docs/ directory
- **Examples**: Review examples/ directory

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

---

Thank you for contributing to ANZ Plus PDF to OFX Converter!
