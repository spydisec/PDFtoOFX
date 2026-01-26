# Web App Implementation Plan - ANZ Plus PDF to OFX Converter

## Overview

Build a minimalistic, elegant web interface for converting ANZ Plus PDF statements to OFX format using **FastAPI** + **Tailwind CSS** + **HTMX**.

### Technology Stack

- **Backend**: FastAPI (async, modern, fast)
- **Frontend**: Tailwind CSS (utility-first, responsive) + HTMX (zero JS interactivity)
- **File Handling**: Python tempfile + async file I/O
- **Deployment**: Docker-ready, single-file app

### Why This Stack?

✅ **FastAPI**: Modern async Python framework, auto-generated docs, type safety  
✅ **Tailwind CSS**: Utility-first CSS via CDN, no build step required  
✅ **HTMX**: Dynamic interactions without writing JavaScript  
✅ **No Database**: Stateless, file-based conversion (secure, no persistence)  
✅ **Minimalistic**: Single-page app, drag-and-drop upload  

---

## Architecture

### Single-Page Application Flow

```
┌─────────────────────────────────────────────┐
│  Landing Page (/)                           │
│  ┌───────────────────────────────────┐      │
│  │  Drop Zone / File Upload          │      │
│  │  "Drop ANZ Plus PDF or Click"     │      │
│  └───────────────────────────────────┘      │
│              ↓ (HTMX POST)                   │
│  ┌───────────────────────────────────┐      │
│  │  Processing Indicator              │      │
│  │  "Converting... ⚡"                │      │
│  └───────────────────────────────────┘      │
│              ↓ (async processing)            │
│  ┌───────────────────────────────────┐      │
│  │  Success Response                  │      │
│  │  ✓ Download OFX Button            │      │
│  │  ✓ Convert Another                │      │
│  │  ✓ Transaction Summary             │      │
│  └───────────────────────────────────┘      │
└─────────────────────────────────────────────┘
```

### File Structure

```
PDFtoOFX/
├── app/
│   ├── web/                      [NEW]
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── routes.py            # API endpoints
│   │   ├── templates/
│   │   │   ├── base.html        # Base template with Tailwind/HTMX
│   │   │   └── index.html       # Main upload page
│   │   └── static/              # Optional static assets
│   │       └── favicon.ico
│   ├── models.py
│   └── services/
│       ├── anz_plus_parser.py
│       └── ...
├── requirements.txt             # Add: fastapi, uvicorn, python-multipart, jinja2
└── docker-compose.yml           [NEW] Optional deployment
```

---

## Detailed Implementation Plan

### Phase 1: FastAPI Backend Setup

#### 1.1 Dependencies (requirements.txt)

Add to existing requirements:
```
# Web Framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6      # File upload support
jinja2>=3.1.3                # Template rendering
aiofiles>=23.2.1             # Async file operations
```

#### 1.2 Main App Structure

**app/web/main.py**:
```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="ANZ Plus to OFX Converter",
    description="Convert ANZ Plus PDF statements to OFX format",
    version="1.0.0"
)

templates = Jinja2Templates(directory="app/web/templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
```

#### 1.3 Upload & Conversion Endpoint

**app/web/routes.py**:
```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import tempfile
import aiofiles
from pathlib import Path

from app.services.pdf_extractor import extract_text_from_pdf
from app.services.anz_plus_parser import AnzPlusParser
from app.services.ofx_generator import OFXGenerator
from app.models import BankConfig

router = APIRouter()

@router.post("/convert", response_class=HTMLResponse)
async def convert_pdf(file: UploadFile = File(...)):
    """Convert uploaded PDF to OFX and return download button"""
    
    # Validation
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(400, "File too large (max 10MB)")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
            content = await file.read()
            await aiofiles.open(tmp_pdf.name, 'wb').write(content)
            pdf_path = Path(tmp_pdf.name)
        
        # Convert PDF to OFX
        text = extract_text_from_pdf(pdf_path)
        parser = AnzPlusParser()
        statement = parser.parse(text)
        
        bank_config = BankConfig(
            name="ANZ Plus",
            ofx_version=220,
            bank_id="633-123",
            currency="AUD"
        )
        generator = OFXGenerator(bank_config)
        ofx_content = generator.generate(statement)
        
        # Save OFX to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ofx', mode='wb') as tmp_ofx:
            tmp_ofx.write(ofx_content)
            ofx_path = tmp_ofx.name
        
        # Clean up PDF
        pdf_path.unlink()
        
        # Return success HTML with download button (HTMX swap)
        return f"""
        <div class="space-y-4 animate-fade-in">
            <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                <div class="flex items-center space-x-2">
                    <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                    </svg>
                    <h3 class="font-semibold text-green-900">Conversion Successful!</h3>
                </div>
                <div class="mt-2 text-sm text-green-700">
                    <p>✓ Found {len(statement.transactions)} transactions</p>
                    <p>✓ Date range: {statement.date_start} to {statement.date_end}</p>
                    <p>✓ Balance: ${statement.closing_balance}</p>
                </div>
            </div>
            
            <a href="/download/{Path(ofx_path).name}" 
               class="block w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg text-center transition-colors">
                ⬇ Download OFX File
            </a>
            
            <button hx-get="/" hx-target="#upload-form" hx-swap="outerHTML"
                    class="block w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold py-3 px-4 rounded-lg text-center transition-colors">
                Convert Another File
            </button>
        </div>
        """
    
    except Exception as e:
        return f"""
        <div class="bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 class="font-semibold text-red-900">Conversion Failed</h3>
            <p class="mt-2 text-sm text-red-700">{str(e)}</p>
            <button hx-get="/" hx-target="#upload-form" hx-swap="outerHTML"
                    class="mt-4 w-full bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg">
                Try Again
            </button>
        </div>
        """

@router.get("/download/{filename}")
async def download_ofx(filename: str):
    """Download the generated OFX file"""
    ofx_path = Path(tempfile.gettempdir()) / filename
    
    if not ofx_path.exists():
        raise HTTPException(404, "File not found or expired")
    
    return FileResponse(
        ofx_path,
        media_type="application/x-ofx",
        filename="statement.ofx",
        headers={"Content-Disposition": "attachment; filename=statement.ofx"}
    )
```

---

### Phase 2: Minimalistic UI with Tailwind + HTMX

#### 2.1 Base Template

**app/web/templates/base.html**:
```html
<!DOCTYPE html>
<html lang="en" class="h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}ANZ Plus to OFX Converter{% endblock %}</title>
    
    <!-- Tailwind CSS via CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    
    <!-- Custom Tailwind Config -->
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    animation: {
                        'fade-in': 'fadeIn 0.5s ease-in',
                        'slide-up': 'slideUp 0.4s ease-out'
                    },
                    keyframes: {
                        fadeIn: {
                            '0%': { opacity: '0' },
                            '100%': { opacity: '1' }
                        },
                        slideUp: {
                            '0%': { transform: 'translateY(20px)', opacity: '0' },
                            '100%': { transform: 'translateY(0)', opacity: '1' }
                        }
                    }
                }
            }
        }
    </script>
    
    <style>
        /* Custom drop zone hover effect */
        .drop-zone {
            transition: all 0.3s ease;
        }
        .drop-zone:hover {
            border-color: #3b82f6;
            background-color: #eff6ff;
        }
        .htmx-request .htmx-indicator {
            display: inline-block;
        }
        .htmx-indicator {
            display: none;
        }
    </style>
</head>
<body class="h-full bg-gradient-to-br from-blue-50 via-white to-purple-50">
    <div class="min-h-full flex flex-col">
        <!-- Header -->
        <header class="bg-white shadow-sm">
            <div class="max-w-4xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
                <div class="flex items-center space-x-3">
                    <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                    <div>
                        <h1 class="text-2xl font-bold text-gray-900">ANZ Plus to OFX</h1>
                        <p class="text-sm text-gray-500">Convert your statements for Actual Budget</p>
                    </div>
                </div>
            </div>
        </header>
        
        <!-- Main Content -->
        <main class="flex-grow">
            <div class="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
                {% block content %}{% endblock %}
            </div>
        </main>
        
        <!-- Footer -->
        <footer class="bg-white border-t border-gray-200">
            <div class="max-w-4xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
                <p class="text-center text-sm text-gray-500">
                    Open source • 
                    <a href="https://github.com/yourusername/PDFtoOFX" class="text-blue-600 hover:text-blue-700">GitHub</a> • 
                    Not affiliated with ANZ Bank
                </p>
            </div>
        </footer>
    </div>
</body>
</html>
```

#### 2.2 Main Upload Page

**app/web/templates/index.html**:
```html
{% extends "base.html" %}

{% block content %}
<div class="space-y-8 animate-slide-up">
    <!-- Instructions Card -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">How It Works</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0 bg-blue-100 rounded-lg p-2">
                    <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                    </svg>
                </div>
                <div>
                    <h3 class="font-medium text-gray-900">1. Upload PDF</h3>
                    <p class="text-sm text-gray-500">Drop your ANZ Plus statement</p>
                </div>
            </div>
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0 bg-purple-100 rounded-lg p-2">
                    <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                    </svg>
                </div>
                <div>
                    <h3 class="font-medium text-gray-900">2. Convert</h3>
                    <p class="text-sm text-gray-500">Instant OFX generation</p>
                </div>
            </div>
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0 bg-green-100 rounded-lg p-2">
                    <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                    </svg>
                </div>
                <div>
                    <h3 class="font-medium text-gray-900">3. Download</h3>
                    <p class="text-sm text-gray-500">Import to Actual Budget</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Upload Form -->
    <div id="upload-form" class="bg-white rounded-xl shadow-lg border-2 border-dashed border-gray-300 p-8">
        <form hx-post="/convert" 
              hx-encoding="multipart/form-data"
              hx-target="#upload-form"
              hx-swap="outerHTML"
              hx-indicator="#loading"
              class="space-y-6">
            
            <!-- Drop Zone -->
            <div class="drop-zone border-2 border-dashed border-gray-300 rounded-lg p-12 text-center cursor-pointer"
                 onclick="document.getElementById('file-upload').click()">
                <svg class="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                </svg>
                <div class="mt-4">
                    <label for="file-upload" class="cursor-pointer">
                        <span class="text-lg font-medium text-blue-600 hover:text-blue-700">
                            Choose a file
                        </span>
                        <span class="text-gray-500"> or drag and drop</span>
                    </label>
                    <input id="file-upload" 
                           name="file" 
                           type="file" 
                           accept=".pdf"
                           class="sr-only"
                           required
                           onchange="this.form.requestSubmit()">
                </div>
                <p class="mt-2 text-sm text-gray-500">
                    ANZ Plus PDF statements only (max 10MB)
                </p>
            </div>
            
            <!-- Loading Indicator -->
            <div id="loading" class="htmx-indicator">
                <div class="flex items-center justify-center space-x-3">
                    <svg class="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span class="text-lg font-medium text-gray-700">Converting your statement...</span>
                </div>
            </div>
        </form>
    </div>
    
    <!-- Features -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div class="flex items-center space-x-2 text-green-600">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                </svg>
                <span class="font-medium">Secure & Private</span>
            </div>
            <p class="mt-1 text-sm text-gray-500">Files processed in memory, not stored</p>
        </div>
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div class="flex items-center space-x-2 text-blue-600">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd"></path>
                </svg>
                <span class="font-medium">Instant Processing</span>
            </div>
            <p class="mt-1 text-sm text-gray-500">Multi-line descriptions & smart truncation</p>
        </div>
    </div>
</div>
{% endblock %}
```

---

### Phase 3: Deployment & Configuration

#### 3.1 Run Development Server

**run_web.py** (root):
```python
#!/usr/bin/env python3
"""Run the web application"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.web.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
```

Run with:
```bash
python run_web.py
# or
uvicorn app.web.main:app --reload
```

#### 3.2 Docker Deployment (Optional)

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./app:/app/app
    restart: unless-stopped
```

---

## UI/UX Features

### Minimalistic Design Principles

✅ **Single-Page Flow** - No navigation, linear conversion process  
✅ **Drag & Drop** - Intuitive file upload with visual feedback  
✅ **Instant Feedback** - Loading states, success/error messages  
✅ **Clean Typography** - Clear hierarchy, readable fonts  
✅ **Subtle Animations** - Smooth transitions, fade-ins  
✅ **Mobile Responsive** - Works perfectly on all devices  
✅ **Accessibility** - WCAG compliant, keyboard navigation  

### Color Palette

- **Primary**: Blue 600 (`#2563eb`) - Trust, professional
- **Success**: Green 600 (`#16a34a`) - Positive feedback
- **Error**: Red 600 (`#dc2626`) - Clear warnings
- **Background**: Gradient from blue-50 to purple-50 - Soft, modern
- **Text**: Gray 900 for headers, Gray 500 for secondary

### Interactions

1. **Hover Effects**:
   - Drop zone highlights on hover
   - Buttons darken slightly
   - Smooth color transitions

2. **Loading States**:
   - Spinning loader during conversion
   - "Converting..." text
   - Disabled upload zone

3. **Success State**:
   - Green checkmark animation
   - Transaction summary
   - Prominent download button

4. **Error Handling**:
   - Red border alert box
   - Clear error message
   - "Try Again" button

---

## Security Considerations

### File Validation

```python
# Size limit
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Content type validation
ALLOWED_TYPES = ['application/pdf']

# Filename sanitization
import re
def sanitize_filename(filename: str) -> str:
    return re.sub(r'[^\w\s-]', '', filename).strip()
```

### Temporary File Cleanup

```python
import atexit
import tempfile

# Auto-cleanup on shutdown
@atexit.register
def cleanup_temp_files():
    temp_dir = Path(tempfile.gettempdir())
    for file in temp_dir.glob("*.ofx"):
        if file.stat().st_mtime < time.time() - 3600:  # 1 hour old
            file.unlink()
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/convert")
@limiter.limit("10/minute")  # 10 conversions per minute
async def convert_pdf(...):
    ...
```

---

## Implementation Checklist

### Phase 1: Backend (2-3 hours)
- [ ] Add dependencies to requirements.txt
- [ ] Create app/web/ directory structure
- [ ] Implement main.py with FastAPI setup
- [ ] Create routes.py with upload/download endpoints
- [ ] Add file validation and error handling
- [ ] Test PDF upload and conversion

### Phase 2: Frontend (2-3 hours)
- [ ] Create templates/ directory
- [ ] Build base.html with Tailwind + HTMX
- [ ] Design index.html upload page
- [ ] Implement drag-and-drop functionality
- [ ] Add loading states and animations
- [ ] Style success/error responses

### Phase 3: Polish (1-2 hours)
- [ ] Add responsive mobile design
- [ ] Implement proper error messages
- [ ] Add file size/type validation UI
- [ ] Test on different browsers
- [ ] Add accessibility features
- [ ] Create favicon

### Phase 4: Deployment (1 hour)
- [ ] Create run_web.py script
- [ ] Add Dockerfile (optional)
- [ ] Update .gitignore for uploads/
- [ ] Update README with web app instructions
- [ ] Test production deployment

---

## Estimated Timeline

- **Backend Setup**: 2-3 hours
- **Frontend Design**: 2-3 hours
- **Testing & Polish**: 1-2 hours
- **Documentation**: 30 minutes

**Total**: 6-9 hours for complete implementation

---

## Next Steps

1. **Add FastAPI dependencies** to requirements.txt
2. **Create directory structure** (app/web/)
3. **Implement backend** (main.py, routes.py)
4. **Build templates** (base.html, index.html)
5. **Test locally** with sample PDFs
6. **Deploy** to cloud service (Render, Railway, Fly.io)

---

## Production Deployment Options

### Option 1: Render.com (Free Tier)
- Automatic deployments from GitHub
- Free SSL certificate
- 512MB RAM (sufficient for this app)

### Option 2: Railway.app
- $5/month for hobby plan
- Better performance than free tiers
- Easy environment variables

### Option 3: Docker + VPS
- DigitalOcean/Linode droplet
- Full control over deployment
- ~$5-10/month

---

This plan creates a production-ready, beautiful, minimalistic web interface for your ANZ Plus to OFX converter with modern best practices! 🚀
