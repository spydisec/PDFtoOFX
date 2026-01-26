"""
Test logging configuration to ensure it works properly
"""
import tempfile
import logging
from pathlib import Path
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.logging_config import setup_logging, get_logger, get_log_level


def test_logging_setup():
    """Test that logging setup works correctly"""
    
    # Use a temporary directory for logs
    with tempfile.TemporaryDirectory() as temp_dir:
        log_dir = Path(temp_dir)
        
        # Test development mode
        print("\n=== Testing Development Mode ===")
        os.environ["ENVIRONMENT"] = "development"
        os.environ["LOG_LEVEL"] = "debug"
        
        setup_logging(log_dir=log_dir, environment="development")
        logger = get_logger(__name__)
        
        # Test different log levels
        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        
        # Test exception logging
        try:
            raise ValueError("Test exception")
        except Exception as e:
            logger.error(f"Caught exception: {e}", exc_info=True)
        
        # Check log files were created
        log_files = list(log_dir.glob("*.log"))
        print(f"Created {len(log_files)} log file(s):")
        for log_file in log_files:
            print(f"  - {log_file.name} ({log_file.stat().st_size} bytes)")
        
        # Test production mode
        print("\n=== Testing Production Mode ===")
        os.environ["ENVIRONMENT"] = "production"
        os.environ["LOG_LEVEL"] = "info"
        
        # Clear handlers to reinitialize
        logging.getLogger().handlers.clear()
        
        setup_logging(log_dir=log_dir, environment="production")
        logger = get_logger(__name__)
        
        logger.info("Production mode test message")
        logger.error("Production mode error message")
        
        # Check updated log files
        log_files = list(log_dir.glob("*.log"))
        print(f"Total log files: {len(log_files)}")
        for log_file in log_files:
            print(f"  - {log_file.name} ({log_file.stat().st_size} bytes)")
            
        # Test log level function
        print("\n=== Testing Log Level Function ===")
        assert get_log_level("development") == logging.INFO
        
        os.environ["LOG_LEVEL"] = "debug"
        assert get_log_level() == logging.DEBUG
        
        os.environ["LOG_LEVEL"] = "error"
        assert get_log_level() == logging.ERROR
        
        print("✅ All log level tests passed")
        
        print("\n=== Logging Test Complete ===")
        print("✅ Logging system is working correctly!")
        
        # Close all log handlers to release file locks
        logging.shutdown()


if __name__ == "__main__":
    test_logging_setup()
