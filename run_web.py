#!/usr/bin/env python3
"""
Run the ANZ Plus to OFX web application

Usage:
    python run_web.py
    
Then open your browser to http://localhost:8000

Environment Variables:
    PORT: Server port (default: 8000)
    HOST: Server host (default: 0.0.0.0)
    WORKERS: Number of worker processes (default: 1 for dev, 4 for production)
    LOG_LEVEL: Log level - debug, info, warning, error, critical (default: info)
    RELOAD: Enable auto-reload on code changes (default: True for dev, False for production)
    ENVIRONMENT: Deployment environment - development or production (default: development)
"""
import os
import uvicorn


def get_config():
    """Get configuration from environment variables with defaults"""
    # Detect environment
    environment = os.getenv("ENVIRONMENT", "development").lower()
    is_production = environment == "production"
    
    # Get configuration with environment-aware defaults
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    workers = int(os.getenv("WORKERS", "4" if is_production else "1"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    reload = os.getenv("RELOAD", "false" if is_production else "true").lower() in ("true", "1", "yes")
    
    return {
        "host": host,
        "port": port,
        "workers": workers,
        "log_level": log_level,
        "reload": reload,
        "environment": environment
    }


if __name__ == "__main__":
    config = get_config()
    
    print("🚀 Starting ANZ Plus to OFX Converter Web App...")
    print(f"📍 Environment: {config['environment']}")
    print(f"📍 Server: http://{config['host']}:{config['port']}")
    print(f"📚 API docs: http://localhost:{config['port']}/api/docs")
    print(f"🔧 Workers: {config['workers']}")
    print(f"📝 Log level: {config['log_level']}")
    print(f"🔄 Auto-reload: {config['reload']}")
    print("\n💡 Press CTRL+C to stop the server\n")
    
    uvicorn.run(
        "app.web.main:app",
        host=config["host"],
        port=config["port"],
        workers=config["workers"] if not config["reload"] else 1,  # workers > 1 incompatible with reload
        reload=config["reload"],
        log_level=config["log_level"],
        access_log=True
    )
