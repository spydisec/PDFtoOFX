"""FastAPI application for ANZ Plus to OFX converter"""
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.web.routes import router
from app.logging_config import setup_logging, get_logger

# Setup logging first
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="ANZ Plus to OFX Converter",
    description="Convert ANZ Plus PDF statements to OFX format for Actual Budget",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

logger.info("FastAPI application initialized")

# Get the templates directory
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Mount static files (for favicon, etc)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.debug(f"Static files mounted from {static_dir}")

# Include API routes
app.include_router(router)


# === Exception Handlers ===

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with logging"""
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else None
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with logging"""
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors(),
            "client": request.client.host if request.client else None
        }
    )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions with full logging"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else None,
            "exception_type": type(exc).__name__
        }
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."}
    )


# === Lifecycle Events ===

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Application startup: ANZ Plus to OFX Converter")
    logger.info(f"Templates directory: {templates_dir}")
    logger.info(f"Static files: {static_dir if static_dir.exists() else 'None'}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Application shutdown")



@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main upload page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "anz-plus-to-ofx"}
