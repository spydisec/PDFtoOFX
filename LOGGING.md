# Logging Configuration

## Overview

The ANZ Plus to OFX Converter includes comprehensive logging to help troubleshoot issues, monitor application health, and track usage patterns. The logging system is designed to work seamlessly in both development and production environments.

## Log Files

All log files are stored in the `logs/` directory (created automatically on first run):

### Development Mode

- **`anzplus_ofx_converter.log`** - Main application log with all messages (INFO and above)
- **`anzplus_ofx_converter_error.log`** - Error and critical messages only

### Production Mode

In addition to the above files:

- **`anzplus_ofx_converter_daily.log`** - Daily rotating log for long-term archival (30 days retention)

## Log Levels

The application supports standard Python logging levels:

- **DEBUG** - Detailed information for diagnosing problems
- **INFO** - Confirmation that things are working as expected
- **WARNING** - Indication that something unexpected happened
- **ERROR** - More serious problem that prevented a function from completing
- **CRITICAL** - Serious error that may prevent the program from continuing

## Configuration

### Environment Variables

Configure logging behavior using environment variables:

```bash
# Set log level (default: info)
export LOG_LEVEL=debug  # Options: debug, info, warning, error, critical

# Set environment mode (default: development)
export ENVIRONMENT=production  # Options: development, production
```

### Development vs Production

**Development Mode** (default):
- Colorized console output for easy reading
- Human-readable log format
- Single log file with rotation
- Debug messages included (if LOG_LEVEL=debug)

**Production Mode** (ENVIRONMENT=production):
- JSON-formatted logs for machine parsing
- Console output in structured JSON
- Multiple log files with rotation
- Daily log archival (30-day retention)
- Better suited for log aggregation services

## Log Format

### Development Format

```
2026-01-26 10:30:45 - app.web.routes - INFO - Conversion request received: filename=statement.pdf
2026-01-26 10:30:46 - app.services.pdf_extractor - INFO - PDF opened successfully: 3 pages
2026-01-26 10:30:47 - app.services.anz_plus_parser - INFO - Found 25 transactions
```

### Production Format (JSON)

```json
{
  "timestamp": "2026-01-26T10:30:45.123456Z",
  "level": "INFO",
  "logger": "app.web.routes",
  "message": "Conversion request received: filename=statement.pdf",
  "module": "routes",
  "function": "convert_pdf",
  "line": 42
}
```

### Error Format (with exception)

```json
{
  "timestamp": "2026-01-26T10:30:48.123456Z",
  "level": "ERROR",
  "logger": "app.web.routes",
  "message": "Conversion failed: Invalid PDF format",
  "module": "routes",
  "function": "convert_pdf",
  "line": 98,
  "exception": {
    "type": "ValueError",
    "message": "Invalid PDF format",
    "traceback": "Traceback (most recent call last):\n  File..."
  }
}
```

## What Gets Logged

### Request Tracking

Every conversion request is logged with:
- Original filename
- File size
- Client IP (if available)
- Request timestamp
- Processing duration

### Processing Steps

Key processing steps are logged:
1. File upload and validation
2. PDF text extraction (page count, character count)
3. Transaction parsing (count, date range)
4. OFX generation (output size)
5. File download events

### Errors and Exceptions

All errors are logged with full context:
- Exception type and message
- Full stack trace
- Request context (URL, method, client IP)
- Additional metadata (filename, file size, etc.)

### Security Events

Security-relevant events are logged:
- Failed filename validation attempts
- Path traversal detection
- Invalid file access attempts
- Expired file access

## Log Rotation

### Application Logs
- Maximum size: 10 MB per file
- Backup count: 5 files
- Total storage: ~50 MB for main log

### Error Logs
- Maximum size: 10 MB per file
- Backup count: 10 files
- Total storage: ~100 MB for error logs

### Daily Logs (Production Only)
- Rotation: Daily at midnight
- Retention: 30 days
- Automatic cleanup of old files

## Integration with Monitoring Services

The JSON logging format in production mode is designed to integrate with popular monitoring services:

### Datadog

```python
# Logs are already in JSON format, ready for Datadog ingestion
# Add Datadog agent configuration to forward logs
```

### AWS CloudWatch

```python
# JSON logs can be sent to CloudWatch using boto3
# Configure CloudWatch agent to tail log files
```

### ELK Stack (Elasticsearch, Logstash, Kibana)

```python
# JSON logs work perfectly with Logstash
# Configure Filebeat to ship logs to Logstash
```

### Sentry

For error tracking, you can integrate Sentry:

```python
# Add to requirements.txt:
# sentry-sdk

# Add to app/web/main.py:
import sentry_sdk
sentry_sdk.init(dsn="YOUR_SENTRY_DSN")
```

## Viewing Logs

### During Development

```bash
# View main log in real-time
tail -f logs/anzplus_ofx_converter.log

# View only errors
tail -f logs/anzplus_ofx_converter_error.log

# Search for specific patterns
grep "ERROR" logs/anzplus_ofx_converter.log

# View colored output in terminal
python run_web.py
```

### In Production (Docker)

```bash
# View container logs (includes application logs)
docker logs anzplus-ofx-converter

# Follow logs in real-time
docker logs -f anzplus-ofx-converter

# View last 100 lines
docker logs --tail 100 anzplus-ofx-converter

# View logs with timestamps
docker logs -t anzplus-ofx-converter
```

### Accessing Log Files in Docker

```bash
# Copy logs from container to host
docker cp anzplus-ofx-converter:/app/logs ./logs

# Or mount logs directory when running container
docker run -v ./logs:/app/logs anzplus-ofx-converter
```

## Troubleshooting

### Common Issues

**No logs being generated:**
- Check that the application has write permissions to the logs directory
- Verify LOG_LEVEL is not set to a level that filters out messages
- Ensure the logging module is imported in main.py

**Log files growing too large:**
- Rotation should handle this automatically
- Check backup count and max file size settings
- Consider lowering LOG_LEVEL in production

**Can't find specific error:**
- Check the error log file specifically
- Search by timestamp or request ID
- Use grep with context: `grep -A 5 -B 5 "error message" logs/*.log`

### Debug Mode

To enable maximum verbosity:

```bash
export LOG_LEVEL=debug
export ENVIRONMENT=development
python run_web.py
```

This will show:
- All HTTP requests
- PDF processing details
- Transaction parsing steps
- OFX generation internals
- File cleanup operations

## Privacy and Security

### PII Handling

The logging system is designed to avoid logging sensitive information:
- ✅ Filename logged (user uploaded)
- ✅ Transaction count logged
- ✅ Date ranges logged
- ❌ Transaction descriptions NOT logged
- ❌ Account balances NOT logged in detail
- ❌ Personal information NOT logged

### Log File Security

Recommendations:
- Restrict access to logs directory (chmod 600 or 700)
- Regularly rotate and archive old logs
- Use encrypted storage for archived logs
- Consider log anonymization for compliance (GDPR, etc.)

## Performance Impact

Logging has minimal performance impact:
- File I/O is buffered and asynchronous
- Log rotation happens in background
- JSON formatting adds ~1-2ms per log entry
- Console output may slow down in high-volume scenarios

For high-traffic deployments:
- Set LOG_LEVEL=warning or higher
- Disable console logging
- Use log aggregation services instead of file-based logging

## Example Logging Usage

### In Application Code

```python
from app.logging_config import get_logger

logger = get_logger(__name__)

# Simple message
logger.info("Processing started")

# With context
logger.info(f"Converted {count} transactions", extra={
    "transaction_count": count,
    "file_size": size,
    "processing_time": duration
})

# Error with exception
try:
    process_file()
except Exception as e:
    logger.error(f"Processing failed: {str(e)}", exc_info=True)
```

### Custom Log Context

```python
from app.logging_config import LogContext, get_logger

logger = get_logger(__name__)

with LogContext(logger, request_id="abc123", user_id="user456"):
    logger.info("Processing request")  # Will include request_id and user_id
```

## Maintenance

### Log Cleanup

Automatic cleanup is handled by rotation, but you can manually clean up:

```bash
# Delete logs older than 30 days
find logs/ -name "*.log*" -mtime +30 -delete

# Compress old logs
find logs/ -name "*.log.*" -exec gzip {} \;

# Archive to S3 (example)
aws s3 sync logs/ s3://my-bucket/logs/$(date +%Y-%m-%d)/ --exclude "*.log"
```

### Monitoring Log Health

```bash
# Check log file sizes
du -sh logs/*

# Count log entries by level
grep -c "ERROR" logs/anzplus_ofx_converter.log
grep -c "WARNING" logs/anzplus_ofx_converter.log

# Find recent errors
tail -100 logs/anzplus_ofx_converter_error.log
```

## Additional Resources

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Logging Best Practices](https://docs.python-guide.org/writing/logging/)
- [Structured Logging](https://www.structlog.org/)
