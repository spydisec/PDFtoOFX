# Web App Quick Start Guide

## 🚀 Running the Web Application

The web application is now **live and running**!

### Access the Application

Open your browser and navigate to:
- **Main App**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

### Usage

1. **Upload PDF**
   - Drag and drop your ANZ Plus statement PDF onto the upload zone
   - Or click to browse and select a file
   - Maximum file size: 10MB

2. **Conversion**
   - The app automatically starts converting when you select a file
   - Watch the progress indicator while processing

3. **Download**
   - View transaction summary (count, date range, balances)
   - Click "Download OFX File" button
   - Import the downloaded file into Actual Budget

4. **Convert Another**
   - Click "Convert Another File" to process additional statements

### Features

✅ **Elegant UI**
- Minimalistic design with Tailwind CSS
- Smooth animations and transitions
- Mobile responsive

✅ **Drag & Drop**
- Intuitive file upload
- Visual feedback on hover

✅ **Real-time Feedback**
- Loading indicators during conversion
- Success/error messages
- Transaction summary display

✅ **Secure**
- Files processed in memory
- Automatically deleted after download
- No data persistence

### Technology Stack

- **Backend**: FastAPI (async Python framework)
- **Frontend**: Tailwind CSS (utility-first CSS)
- **Interactivity**: HTMX (zero-JS dynamic updates)
- **Server**: Uvicorn (ASGI server with auto-reload)

### Development Mode

The server is running with **auto-reload** enabled, which means:
- Any code changes will automatically restart the server
- No need to manually stop/start during development
- Changes are reflected immediately

### Stop the Server

Press `CTRL+C` in the terminal running `python run_web.py`

### Deployment

For production deployment, see [WEB_APP_PLAN.md](WEB_APP_PLAN.md) for options:
- Render.com (free tier)
- Railway.app ($5/month)
- Docker + VPS (full control)

---

## 📸 Screenshots

### Main Upload Page
- Clean, modern design with gradient background
- Three-step process explained clearly
- Drag-and-drop upload zone
- Feature cards showcasing security and speed

### Success State
- Green success banner with checkmark
- Transaction statistics (count, date range, balances)
- Prominent download button
- "Convert Another" option

### Error Handling
- Red error banner with clear message
- "Try Again" button to retry
- Detailed error messages for debugging

---

## 🎨 UI/UX Highlights

### Color Palette
- **Primary**: Blue 600 - Trust, professional
- **Success**: Green 600 - Positive feedback  
- **Error**: Red 600 - Clear warnings
- **Background**: Gradient blue-50 → purple-50

### Animations
- Fade-in effects for dynamic content
- Slide-up animation on page load
- Smooth hover transitions
- Spinning loader during processing

### Accessibility
- Semantic HTML structure
- ARIA labels where needed
- Keyboard navigation support
- Mobile-friendly touch targets

---

## 🔧 Customization

### Change Port

Edit [run_web.py](run_web.py):
```python
uvicorn.run(
    "app.web.main:app",
    host="0.0.0.0",
    port=3000,  # Change this
    reload=True
)
```

### Update GitHub Link

Edit templates to replace `yourusername` with your actual GitHub username:
- [app/web/templates/base.html](app/web/templates/base.html)

### Modify File Size Limit

Edit [app/web/routes.py](app/web/routes.py):
```python
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
```

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Kill process on port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Use different port
uvicorn app.web.main:app --port 8001
```

### Module Not Found Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Template Not Found

Make sure you're running from the project root:
```bash
cd D:\Github\PDFtoOFX
python run_web.py
```

---

**Enjoy your minimalistic, elegant ANZ Plus to OFX converter! 🎉**
