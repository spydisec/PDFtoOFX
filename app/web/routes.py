"""API routes for PDF to OFX conversion"""
import re
import tempfile
import time
import secrets
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from starlette.background import BackgroundTask

from app.services.pdf_extractor import extract_text_from_pdf
from app.services.anz_plus_parser import AnzPlusParser
from app.services.ofx_generator import OFXGenerator
from app.models import BankConfig
from app.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# File upload constraints
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.get("/health")
async def health_check():
    """
    Health check endpoint for Docker and orchestration tools
    
    Returns:
        JSON response with service status
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "anzplus-ofx-converter",
            "version": "1.0.0"
        }
    )


@router.post("/convert", response_class=HTMLResponse)
async def convert_pdf(file: UploadFile = File(...)):
    """
    Convert uploaded PDF to OFX format
    
    Returns HTML response with download button (for HTMX swap)
    """
    logger.info(f"Conversion request received: filename={file.filename}")
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        logger.warning(f"Invalid file type uploaded: {file.filename}")
        return error_response("Only PDF files are supported. Please upload an ANZ Plus statement PDF.")
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    logger.debug(f"File read successfully: size={file_size} bytes")
    
    # Validate file size
    if file_size > MAX_FILE_SIZE:
        logger.warning(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})")
        return error_response(f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB.")
    
    if file_size == 0:
        logger.warning(f"Empty file uploaded: {file.filename}")
        return error_response("File is empty. Please upload a valid ANZ Plus statement PDF.")
    
    pdf_path = None
    ofx_path = None
    
    try:
        # Save uploaded PDF to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
            tmp_pdf.write(content)
            pdf_path = Path(tmp_pdf.name)
        
        logger.debug(f"PDF saved to temporary file: {pdf_path}")
        
        # Extract text from PDF
        logger.info("Extracting text from PDF...")
        text = extract_text_from_pdf(pdf_path)
        
        if not text or len(text.strip()) < 100:
            logger.error(f"Failed to extract text from PDF: text_length={len(text) if text else 0}")
            return error_response("Could not extract text from PDF. Please ensure it's a valid ANZ Plus statement.")
        
        logger.debug(f"Text extracted successfully: {len(text)} characters")
        
        # Parse transactions
        logger.info("Parsing transactions...")
        parser = AnzPlusParser()
        statement = parser.parse(text)
        
        if not statement.transactions:
            logger.warning("No transactions found in PDF")
            return error_response("No transactions found in the PDF. Please check if this is a valid ANZ Plus statement.")
        
        logger.info(f"Parsed {len(statement.transactions)} transactions")
        
        # Generate OFX
        logger.info("Generating OFX content...")
        bank_config = BankConfig(
            name="ANZ Plus",
            ofx_version=220,
            bank_id="633-123",
            currency="AUD"
        )
        generator = OFXGenerator(bank_config)
        ofx_content = generator.generate(statement)
        
        # Generate secure filename: ofx_YYYYMMDD_HHMMSS_<random>.ofx
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = secrets.token_hex(6)  # 12 hex characters
        filename = f"ofx_{timestamp}_{random_suffix}.ofx"
        
        # Save OFX to temporary file
        temp_dir = Path(tempfile.gettempdir())
        ofx_path = temp_dir / filename
        ofx_path.write_bytes(ofx_content)
        
        logger.info(f"OFX file created successfully: {filename}")
        logger.debug(f"OFX file path: {ofx_path}")
        
        # Format date range
        date_start = statement.date_start.strftime('%d %b %Y') if statement.date_start else 'N/A'
        date_end = statement.date_end.strftime('%d %b %Y') if statement.date_end else 'N/A'
        
        # Format balances with None handling
        opening_balance = f"{statement.opening_balance:.2f}" if statement.opening_balance is not None else "N/A"
        closing_balance = f"{statement.closing_balance:.2f}" if statement.closing_balance is not None else "N/A"
        
        logger.info(
            f"Conversion successful: transactions={len(statement.transactions)}, "
            f"date_range={date_start} to {date_end}, "
            f"opening_balance={opening_balance}, closing_balance={closing_balance}"
        )
        
        # Return success HTML
        return success_response(
            filename=filename,
            transaction_count=len(statement.transactions),
            date_start=date_start,
            date_end=date_end,
            opening_balance=opening_balance,
            closing_balance=closing_balance
        )
    
    except Exception as e:
        logger.error(
            f"Conversion failed: {str(e)}",
            exc_info=True,
            extra={
                "filename": file.filename,
                "file_size": len(content),
                "exception_type": type(e).__name__
            }
        )
        return error_response(f"Conversion failed: {str(e)}")
    
    finally:
        # Clean up PDF file
        if pdf_path and pdf_path.exists():
            try:
                pdf_path.unlink()
                logger.debug(f"Temporary PDF file cleaned up: {pdf_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary PDF file: {e}")


def validate_safe_filename(filename: str) -> str:
    """
    Validate and sanitize filename to prevent path traversal attacks (CWE-22)
    
    Args:
        filename: User-provided filename
        
    Returns:
        Validated filename
        
    Raises:
        HTTPException: If filename is invalid or potentially malicious
    """
    # Rule 1: Must not be empty
    if not filename or not filename.strip():
        raise HTTPException(status_code=400, detail="Filename cannot be empty")
    
    # Rule 2: Must match expected pattern exactly
    # Expected format: ofx_YYYYMMDD_HHMMSS_<random>.ofx
    pattern = r'^ofx_\d{8}_\d{6}_[a-f0-9]{6,12}\.ofx$'
    if not re.match(pattern, filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename format. Expected format: ofx_YYYYMMDD_HHMMSS_random.ofx"
        )
    
    # Rule 3: No path separators (belt and suspenders)
    if '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Filename cannot contain path separators")
    
    # Rule 4: No multiple dots or parent directory references
    if '..' in filename or filename.count('.') > 1:
        raise HTTPException(status_code=400, detail="Invalid filename pattern")
    
    # Rule 5: Must be within reasonable length
    if len(filename) > 100:
        raise HTTPException(status_code=400, detail="Filename too long")
    
    # Rule 6: Only allow ASCII alphanumeric, underscore, hyphen, and single dot
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.')
    if not all(c in allowed_chars for c in filename):
        raise HTTPException(status_code=400, detail="Filename contains invalid characters")
    
    return filename


@router.get("/download/{filename}")
async def download_ofx(filename: str):
    """
    Download the generated OFX file
    
    Security: Validates filename to prevent path traversal attacks (CWE-22)
    Uses strict allowlist validation and path resolution to ensure file access is safe
    """
    logger.info(f"Download request: filename={filename}")
    
    # Security: Validate filename with strict allowlist approach
    try:
        safe_filename = validate_safe_filename(filename)
    except HTTPException as e:
        logger.warning(f"Invalid filename validation failed: {filename}, error={e.detail}")
        raise
    
    # Construct path safely
    temp_dir = Path(tempfile.gettempdir())
    ofx_path = temp_dir / safe_filename
    
    # Security: Ensure resolved path is still within temp directory
    # This prevents symlink attacks and path traversal
    try:
        ofx_path_resolved = ofx_path.resolve()
        temp_dir_resolved = temp_dir.resolve()
        
        # Ensure the file is actually in the temp directory
        if not str(ofx_path_resolved).startswith(str(temp_dir_resolved)):
            logger.error(f"Path traversal attempt detected: {filename}")
            raise HTTPException(status_code=403, detail="Access denied")
    except (ValueError, OSError, RuntimeError) as e:
        logger.error(f"Invalid file path: {filename}, error={str(e)}")
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    # Use the resolved path for further operations
    ofx_path = ofx_path_resolved
    
    if not ofx_path.exists():
        logger.warning(f"File not found: {filename}")
        raise HTTPException(status_code=404, detail="File not found or expired. Please convert your PDF again.")
    
    # Security: Verify it's actually a file, not a directory
    if not ofx_path.is_file():
        logger.error(f"Invalid file type (not a file): {filename}")
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Check if file is too old (1 hour)
    file_age = time.time() - ofx_path.stat().st_mtime
    if file_age > 3600:
        logger.info(f"File expired (age: {file_age}s): {filename}")
        ofx_path.unlink()
        raise HTTPException(status_code=404, detail="File has expired. Please convert your PDF again.")
    
    logger.info(f"File download started: {filename}")
    
    return FileResponse(
        path=ofx_path,
        media_type="application/x-ofx",
        filename="anz_plus_statement.ofx",
        headers={
            "Content-Disposition": "attachment; filename=anz_plus_statement.ofx",
            "Cache-Control": "no-cache"
        },
        background=BackgroundTask(cleanup_file, ofx_path)
    )


def cleanup_file(file_path: Path):
    """Background task to delete file after download"""
    try:
        if file_path.exists():
            time.sleep(1)  # Give time for download to complete
            file_path.unlink()
            logger.debug(f"File cleaned up after download: {file_path.name}")
    except Exception as e:
        logger.warning(f"Failed to clean up file {file_path.name}: {e}")


def success_response(filename: str, transaction_count: int, date_start: str, 
                     date_end: str, opening_balance: str, closing_balance: str) -> str:
    """Generate success HTML response"""
    return f"""
    <div class="space-y-4 animate-fade-in">
        <div class="bg-green-50 border border-green-200 rounded-lg p-6">
            <div class="flex items-center space-x-3 mb-4">
                <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                <h3 class="text-lg font-semibold text-green-900">Conversion Successful!</h3>
            </div>
            <div class="grid grid-cols-2 gap-3 text-sm">
                <div class="bg-white rounded-md p-3">
                    <p class="text-gray-500 text-xs">Transactions</p>
                    <p class="font-semibold text-gray-900 text-lg">{transaction_count}</p>
                </div>
                <div class="bg-white rounded-md p-3">
                    <p class="text-gray-500 text-xs">Date Range</p>
                    <p class="font-semibold text-gray-900">{date_start}</p>
                    <p class="font-semibold text-gray-900">{date_end}</p>
                </div>
                <div class="bg-white rounded-md p-3">
                    <p class="text-gray-500 text-xs">Opening Balance</p>
                    <p class="font-semibold text-gray-900">${opening_balance}</p>
                </div>
                <div class="bg-white rounded-md p-3">
                    <p class="text-gray-500 text-xs">Closing Balance</p>
                    <p class="font-semibold text-gray-900">${closing_balance}</p>
                </div>
            </div>
        </div>
        
        <a href="/download/{filename}" 
           class="block w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-6 rounded-lg text-center transition-colors shadow-lg hover:shadow-xl">
            <div class="flex items-center justify-center space-x-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                </svg>
                <span>Download OFX File</span>
            </div>
        </a>
        
        <button onclick="location.reload()" 
                class="block w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold py-3 px-6 rounded-lg text-center transition-colors">
            Convert Another File
        </button>
    </div>
    """


def error_response(message: str) -> str:
    """Generate error HTML response"""
    return f"""
    <div class="bg-red-50 border-2 border-red-200 rounded-lg p-6 animate-fade-in">
        <div class="flex items-start space-x-3">
            <svg class="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div class="flex-1">
                <h3 class="font-semibold text-red-900 mb-2">Conversion Failed</h3>
                <p class="text-sm text-red-700">{message}</p>
            </div>
        </div>
        <button onclick="location.reload()" 
                class="mt-4 w-full bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors">
            Try Again
        </button>
    </div>
    """
