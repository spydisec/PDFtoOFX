"""FastAPI application for ANZ Plus to OFX converter"""
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.web.routes import router

app = FastAPI(
    title="ANZ Plus to OFX Converter",
    description="Convert ANZ Plus PDF statements to OFX format for Actual Budget",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Get the templates directory
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Mount static files (for favicon, etc)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include API routes
app.include_router(router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main upload page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "anz-plus-to-ofx"}
