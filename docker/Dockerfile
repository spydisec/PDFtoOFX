# Multi-stage Dockerfile for ANZ Plus to OFX Converter
# Uses Python 3.14 Alpine for minimal image size and security
# Security: Pinned to specific Alpine version for reproducibility and security updates

# ===========================
# Stage 1: Builder
# ===========================
FROM python:3.14-alpine3.21 AS builder

# Security: Upgrade all packages to latest versions
RUN apk upgrade --no-cache

# Install build dependencies for Python packages
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers \
    g++ \
    make \
    libffi-dev

# Set working directory
WORKDIR /build

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ===========================
# Stage 2: Runtime
# ===========================
FROM python:3.14-alpine3.21

# Security: Upgrade all packages to latest versions
RUN apk upgrade --no-cache

# Add labels for metadata and security
LABEL maintainer="spydisec" \
      description="ANZ Plus to OFX Converter - Convert ANZ Plus bank statements to OFX format" \
      version="1.0.1" \
      org.opencontainers.image.source="https://github.com/spydisec/PDFtoOFX" \
      org.opencontainers.image.documentation="https://github.com/spydisec/PDFtoOFX/blob/main/README.md" \
      org.opencontainers.image.licenses="MIT"

# Create non-root user for security
RUN adduser -D -h /app -s /bin/sh appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser run_web.py .
COPY --chown=appuser:appuser requirements.txt .

# Switch to non-root user
USER appuser

# Environment variables with defaults
# Security: PYTHONDONTWRITEBYTECODE prevents .pyc file creation
# Security: PYTHONUNBUFFERED ensures logs are flushed immediately
ENV ENVIRONMENT=production \
    PORT=8000 \
    HOST=0.0.0.0 \
    WORKERS=4 \
    LOG_LEVEL=info \
    RELOAD=false \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
# Check every 30 seconds, timeout 10 seconds, 3 retries before unhealthy
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=5s \
    CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT}/health || exit 1

# Run the application
CMD ["python", "run_web.py"]
