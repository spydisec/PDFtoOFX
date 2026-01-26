#!/usr/bin/env python3
"""
Run the ANZ Plus to OFX web application

Usage:
    python run_web.py
    
Then open your browser to http://localhost:8000
"""
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting ANZ Plus to OFX Converter Web App...")
    print("📍 Open your browser to: http://localhost:8000")
    print("📚 API documentation: http://localhost:8000/api/docs")
    print("\n💡 Press CTRL+C to stop the server\n")
    
    uvicorn.run(
        "app.web.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info",
        access_log=True
    )
