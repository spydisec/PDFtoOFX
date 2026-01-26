"""API routes for PDF to OFX conversion"""
import tempfile
import time
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from starlette.background import BackgroundTask

from app.services.pdf_extractor import extract_text_from_pdf
from app.services.anz_plus_parser import AnzPlusParser
from app.services.ofx_generator import OFXGenerator
from app.models import BankConfig

router = APIRouter()

# File upload constraints
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/convert", response_class=HTMLResponse)
async def convert_pdf(file: UploadFile = File(...)):
    """
    Convert uploaded PDF to OFX format
    
    Returns HTML response with download button (for HTMX swap)
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        return error_response("Only PDF files are supported. Please upload an ANZ Plus statement PDF.")
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        return error_response(f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB.")
    
    if len(content) == 0:
        return error_response("File is empty. Please upload a valid ANZ Plus statement PDF.")
    
    pdf_path = None
    ofx_path = None
    
    try:
        # Save uploaded PDF to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
            tmp_pdf.write(content)
            pdf_path = Path(tmp_pdf.name)
        
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_path)
        
        if not text or len(text.strip()) < 100:
            return error_response("Could not extract text from PDF. Please ensure it's a valid ANZ Plus statement.")
        
        # Parse transactions
        parser = AnzPlusParser()
        statement = parser.parse(text)
        
        if not statement.transactions:
            return error_response("No transactions found in the PDF. Please check if this is a valid ANZ Plus statement.")
        
        # Generate OFX
        bank_config = BankConfig(
            name="ANZ Plus",
            ofx_version=220,
            bank_id="633-123",
            currency="AUD"
        )
        generator = OFXGenerator(bank_config)
        ofx_content = generator.generate(statement)
        
        # Save OFX to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ofx', mode='wb') as tmp_ofx:
            tmp_ofx.write(ofx_content)
            ofx_path = Path(tmp_ofx.name)
        
        # Format date range
        date_start = statement.date_start.strftime('%d %b %Y') if statement.date_start else 'N/A'
        date_end = statement.date_end.strftime('%d %b %Y') if statement.date_end else 'N/A'
        
        # Return success HTML
        return success_response(
            filename=ofx_path.name,
            transaction_count=len(statement.transactions),
            date_start=date_start,
            date_end=date_end,
            opening_balance=f"{statement.opening_balance:.2f}",
            closing_balance=f"{statement.closing_balance:.2f}"
        )
    
    except Exception as e:
        return error_response(f"Conversion failed: {str(e)}")
    
    finally:
        # Clean up PDF file
        if pdf_path and pdf_path.exists():
            try:
                pdf_path.unlink()
            except:
                pass


@router.get("/download/{filename}")
async def download_ofx(filename: str):
    """Download the generated OFX file"""
    # Security: only allow filenames without path separators
    if '/' in filename or '\\' in filename or '..' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    ofx_path = Path(tempfile.gettempdir()) / filename
    
    if not ofx_path.exists():
        raise HTTPException(status_code=404, detail="File not found or expired. Please convert your PDF again.")
    
    # Check if file is too old (1 hour)
    if time.time() - ofx_path.stat().st_mtime > 3600:
        ofx_path.unlink()
        raise HTTPException(status_code=404, detail="File has expired. Please convert your PDF again.")
    
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
    except:
        pass


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
