# Project Reorganization Plan - ANZ Plus PDF to OFX Converter

## Current State Analysis

### Issues Identified
1. ❌ Multiple README files (README.md, README_CONVERTER.md, files/README.md)
2. ❌ Documentation scattered in `files/` directory
3. ❌ No clear indication this is ANZ Plus specific
4. ❌ Example OFX files at root level (OFXData.ofx, up2026-01-01.ofx)
5. ❌ Test output files cluttering root (test_output.ofx, test_output_improved.ofx, test_output_final.ofx)
6. ❌ Implementation summary not in proper docs location
7. ❌ Missing LICENSE file for open source
8. ❌ No clear project scope in main README

### Current Structure
```
PDFtoOFX/
├── README.md                    (empty/minimal)
├── README_CONVERTER.md          (detailed usage)
├── IMPLEMENTATION_SUMMARY.md    (technical details)
├── convert_pdf.py               (CLI tool)
├── pyproject.toml               ✓ Good
├── requirements.txt             ✓ Good
├── requirements-dev.txt         ✓ Good
├── OFXData.ofx                  (example - should move)
├── up2026-01-01.ofx            (example - should move)
├── test_output*.ofx            (3 files - should delete/ignore)
│
├── app/                         ✓ Good
│   ├── models.py
│   └── services/
│       ├── anz_plus_parser.py
│       ├── fitid_generator.py
│       ├── ofx_generator.py
│       └── pdf_extractor.py
│
├── tests/                       ✓ Good
│   └── test_converter.py
│
├── files/                       ❌ Should be docs/
│   ├── AI_IMPLEMENTATION_PROMPTS.md
│   ├── example_output.ofx
│   ├── IMPLEMENTATION_GUIDE.md
│   ├── INDEX.md
│   ├── PROJECT_SUMMARY.md
│   ├── QUICKSTART.md
│   └── README.md
│
└── examplepdfs/                 ❌ Should be examples/
    └── 904f7e02-886c-470e-8c00-a93f3d428173.pdf
```

---

## Reorganization Plan

### Phase 1: Create New Directory Structure

#### New Structure
```
PDFtoOFX/
├── README.md                    [NEW] Main project readme - ANZ Plus focus
├── LICENSE                      [NEW] MIT or Apache 2.0
├── .gitignore                   [UPDATE] Ignore test outputs
├── pyproject.toml               [KEEP]
├── requirements.txt             [KEEP]
├── requirements-dev.txt         [KEEP]
├── convert_pdf.py               [KEEP] CLI entry point
│
├── app/                         [KEEP] Application code
│   ├── __init__.py
│   ├── models.py
│   └── services/
│       ├── __init__.py
│       ├── anz_plus_parser.py
│       ├── fitid_generator.py
│       ├── ofx_generator.py
│       └── pdf_extractor.py
│
├── tests/                       [KEEP] Test suite
│   ├── __init__.py
│   └── test_converter.py
│
├── docs/                        [NEW] All documentation
│   ├── QUICKSTART.md           [MOVE from files/]
│   ├── IMPLEMENTATION_GUIDE.md [MOVE from files/]
│   ├── PROJECT_SUMMARY.md      [MOVE from files/]
│   ├── IMPLEMENTATION_SUMMARY.md [MOVE from root]
│   ├── AI_PROMPTS.md           [RENAME from AI_IMPLEMENTATION_PROMPTS.md]
│   └── DEVELOPMENT.md          [NEW] Contributing guide
│
└── examples/                    [NEW] Example files
    ├── pdfs/
    │   └── sample_anz_plus.pdf [RENAME from 904f7e02-...]
    └── outputs/
        ├── example_sgml.ofx    [MOVE from files/example_output.ofx]
        ├── example_xml.ofx     [MOVE from up2026-01-01.ofx]
        └── .gitkeep
```

### Phase 2: File Operations

#### Create New Directories
- [ ] Create `docs/` directory
- [ ] Create `examples/` directory
- [ ] Create `examples/pdfs/` directory
- [ ] Create `examples/outputs/` directory

#### Move Documentation Files
- [ ] Move `files/*.md` → `docs/`
- [ ] Move `IMPLEMENTATION_SUMMARY.md` → `docs/`
- [ ] Rename `files/AI_IMPLEMENTATION_PROMPTS.md` → `docs/AI_PROMPTS.md`
- [ ] Delete `files/README.md` (redundant)
- [ ] Delete `files/INDEX.md` (redundant)
- [ ] Delete `README_CONVERTER.md` (merge into main README)

#### Move Example Files
- [ ] Move `examplepdfs/904f7e02-886c-470e-8c00-a93f3d428173.pdf` → `examples/pdfs/sample_anz_plus.pdf`
- [ ] Move `files/example_output.ofx` → `examples/outputs/example_sgml.ofx`
- [ ] Move `up2026-01-01.ofx` → `examples/outputs/example_xml.ofx`
- [ ] Move `OFXData.ofx` → `examples/outputs/` (if needed)

#### Delete Temporary Files
- [ ] Delete `test_output.ofx`
- [ ] Delete `test_output_improved.ofx`
- [ ] Delete `test_output_final.ofx`

#### Delete Empty Directories
- [ ] Remove `files/` directory
- [ ] Remove `examplepdfs/` directory

### Phase 3: Create New Files

#### Main README.md
Content should include:
- Clear title: "ANZ Plus PDF to OFX Converter"
- Scope: "Converts ANZ Plus bank statement PDFs to OFX format for Actual Budget"
- Features list (multi-line capture, smart truncation, balance-based detection)
- Quick start (installation, usage)
- Examples
- Link to docs/ for detailed guides
- License badge
- Contribution guidelines link

#### LICENSE
- Choose license: MIT (recommended for open source tools)
- Standard MIT license text

#### docs/DEVELOPMENT.md
- How to contribute
- Development setup
- Running tests
- Code style guidelines
- Pull request process

#### .gitignore Updates
Add:
```
# Test outputs
test_output*.ofx
*.ofx  # Ignore all OFX files except in examples/

# Python cache
__pycache__/
*.pyc
.pytest_cache/

# Virtual environments
.venv/
venv/
env/

# IDE
.vscode/
.idea/
*.swp
```

### Phase 4: Update Existing Files

#### pyproject.toml
Update metadata:
```toml
name = "anz-plus-to-ofx"
description = "Convert ANZ Plus bank statement PDFs to OFX format for Actual Budget"
keywords = ["anz", "anz-plus", "ofx", "pdf", "banking", "actual-budget"]
```

#### convert_pdf.py
Update help text to mention ANZ Plus specifically

#### tests/test_converter.py
Update test file paths:
- `examplepdfs/` → `examples/pdfs/`

---

## Implementation Steps

### Step 1: Backup
```bash
git add .
git commit -m "Checkpoint before reorganization"
```

### Step 2: Create Structure
```powershell
New-Item -Path "docs" -ItemType Directory
New-Item -Path "examples" -ItemType Directory
New-Item -Path "examples/pdfs" -ItemType Directory
New-Item -Path "examples/outputs" -ItemType Directory
```

### Step 3: Move Documentation
```powershell
Move-Item files/*.md docs/
Move-Item IMPLEMENTATION_SUMMARY.md docs/
Rename-Item docs/AI_IMPLEMENTATION_PROMPTS.md AI_PROMPTS.md
Remove-Item files/README.md
Remove-Item files/INDEX.md
```

### Step 4: Move Examples
```powershell
Move-Item examplepdfs/904f7e02-886c-470e-8c00-a93f3d428173.pdf examples/pdfs/sample_anz_plus.pdf
Move-Item files/example_output.ofx examples/outputs/example_sgml.ofx
Move-Item up2026-01-01.ofx examples/outputs/example_xml.ofx
Move-Item OFXData.ofx examples/outputs/
```

### Step 5: Cleanup
```powershell
Remove-Item test_output*.ofx
Remove-Item files/
Remove-Item examplepdfs/
```

### Step 6: Create New Files
- Write new README.md
- Add LICENSE
- Create docs/DEVELOPMENT.md
- Update .gitignore

### Step 7: Update References
- Update test file paths in test_converter.py
- Update example paths in documentation
- Update pyproject.toml metadata

### Step 8: Verify
```bash
python -m pytest tests/
python convert_pdf.py examples/pdfs/sample_anz_plus.pdf test.ofx
```

---

## Benefits of New Structure

✅ **Clear Purpose**: Main README immediately shows ANZ Plus focus  
✅ **Professional**: Standard open-source project layout  
✅ **Organized Docs**: All documentation in `docs/` directory  
✅ **Clean Root**: Only essential files in root directory  
✅ **Better Examples**: Clear separation of sample inputs/outputs  
✅ **Contribution Ready**: LICENSE and DEVELOPMENT.md for contributors  
✅ **Discoverable**: Keywords in pyproject.toml help users find it  
✅ **Maintainable**: Logical structure easier to navigate  

---

## Post-Reorganization Checklist

- [ ] All tests still pass
- [ ] Example conversion still works
- [ ] Documentation links are correct
- [ ] README.md is clear and informative
- [ ] LICENSE file is present
- [ ] .gitignore covers all temporary files
- [ ] Project can be installed with `pip install -e .`
- [ ] Project structure follows Python best practices
- [ ] Ready for GitHub publication

---

## Timeline

- **Phase 1-2**: 15 minutes (create dirs, move files)
- **Phase 3**: 30 minutes (write new content)
- **Phase 4**: 15 minutes (update references)
- **Total**: ~1 hour for complete reorganization

---

## Next Steps After Reorganization

1. Add GitHub Actions for CI/CD
2. Add badges to README (tests, coverage, license)
3. Create CHANGELOG.md
4. Tag first release (v0.1.0)
5. Publish to PyPI (optional)
6. Add bank-specific parser architecture for future banks

---

This plan transforms the project into a professional, maintainable, open-source repository specifically focused on ANZ Plus PDF to OFX conversion.
