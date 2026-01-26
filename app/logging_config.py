"""
Centralized logging configuration for ANZ Plus to OFX Converter

This module provides structured logging with:
- File-based logging with rotation
- Console logging with color support
- Different log levels for development vs production
- JSON formatting for production monitoring
- Exception tracking with full stack traces
"""
import logging
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Optional
import os
import json


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging in production"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)  # type: ignore
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output in development"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def get_log_level(environment: Optional[str] = None) -> int:
    """
    Get appropriate log level based on environment
    
    Args:
        environment: Environment name (development/production)
        
    Returns:
        Logging level constant
    """
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development").lower()
    
    log_level_str = os.getenv("LOG_LEVEL", "info").upper()
    
    # Map string to logging constant
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    
    return level_map.get(log_level_str, logging.INFO)


def setup_logging(
    app_name: str = "anzplus_ofx_converter",
    log_dir: Optional[Path] = None,
    environment: Optional[str] = None
) -> logging.Logger:
    """
    Configure application-wide logging
    
    Args:
        app_name: Name of the application (used for log files)
        log_dir: Directory to store log files (defaults to ./logs)
        environment: Environment name (development/production)
        
    Returns:
        Configured root logger
    """
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development").lower()
    
    is_production = environment == "production"
    
    # Get log level
    log_level = get_log_level(environment)
    
    # Create logs directory if not specified
    if log_dir is None:
        log_dir = Path.cwd() / "logs"
    
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # === Console Handler ===
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if is_production:
        # JSON format for production (easier parsing by log aggregators)
        console_formatter = JSONFormatter()
    else:
        # Colored format for development
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # === File Handlers ===
    
    # 1. Main application log (all messages)
    app_log_file = log_dir / f"{app_name}.log"
    app_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    app_handler.setLevel(log_level)
    
    if is_production:
        app_formatter = JSONFormatter()
    else:
        app_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    app_handler.setFormatter(app_formatter)
    root_logger.addHandler(app_handler)
    
    # 2. Error log (errors and critical only)
    error_log_file = log_dir / f"{app_name}_error.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,  # Keep more error logs
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    
    if is_production:
        error_formatter = JSONFormatter()
    else:
        error_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d]\n'
                '%(message)s\n'
                '%(pathname)s:%(lineno)d',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)
    
    # 3. Daily rotating log (for long-term archival)
    if is_production:
        daily_log_file = log_dir / f"{app_name}_daily.log"
        daily_handler = TimedRotatingFileHandler(
            daily_log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days
            encoding='utf-8'
        )
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(daily_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured: environment={environment}, level={logging.getLevelName(log_level)}, "
        f"log_dir={log_dir}"
    )
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Context manager for additional logging context
class LogContext:
    """Context manager to add extra fields to log records"""
    
    def __init__(self, logger: logging.Logger, **kwargs):
        """
        Initialize log context
        
        Args:
            logger: Logger instance
            **kwargs: Extra fields to add to log records
        """
        self.logger = logger
        self.extra_fields = kwargs
        self.old_factory = logging.getLogRecordFactory()
    
    def __enter__(self):
        """Enter context"""
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            record.extra_fields = self.extra_fields
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context"""
        logging.setLogRecordFactory(self.old_factory)
