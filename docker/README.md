# Docker Documentation for ANZ Plus to OFX Converter

Simple guide for using the ANZ Plus to OFX Converter Docker image.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Building Locally (Optional)](#building-locally-optional)
- [Running the Container](#running-the-container)
- [Environment Variables](#environment-variables)
- [Docker Compose](#docker-compose)
- [Multi-Architecture Support](#multi-architecture-support)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

**Official Docker image** is automatically built and published via GitHub Actions for every release.

```bash
# Pull the latest image (recommended)
docker pull spydisec/anzplus-ofx-converter:latest

# Run the container
docker run -d -p 8000:8000 spydisec/anzplus-ofx-converter:latest

# Open your browser
# http://localhost:8000
```

**Supported Architectures:**
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64/Apple Silicon)

## 🛠️ Building Locally (Optional)

Most users should use the official image. For development or testing:

```powershell
# Windows PowerShell
.\docker\build-local.ps1

# Linux/macOS
docker build -f docker/Dockerfile -t anzplus-ofx:local .
```

This creates a local image: `anzplus-ofx:local`

## 🐳 Running the Container

### Quick Run

```bash
# Pull and run the latest image
docker pull spydisec/anzplus-ofx-converter:latest
docker run -d -p 8000:8000 spydisec/anzplus-ofx-converter:latest

# Open http://localhost:8000
```

### Production Run

```bash
docker run -d \
  --name anzplus-ofx-converter \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e WORKERS=4 \
  -e LOG_LEVEL=info \
  --restart unless-stopped \
  spydisec/anzplus-ofx-converter:latest
```

### Development Mode

```bash
docker run -d \
  -p 8000:8000 \
  -e ENVIRONMENT=development \
  -e LOG_LEVEL=debug \
  anzplus-ofx:local
```

## ⚙️ Environment Variables

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `ENVIRONMENT` | Deployment environment | `production` | `development`, `production` |
| `PORT` | Server port inside container | `8000` | Any port |
| `HOST` | Server host binding | `0.0.0.0` | IP address or `0.0.0.0` |
| `WORKERS` | Number of Uvicorn workers | `4` (prod) / `1` (dev) | 1-16 |
| `LOG_LEVEL` | Logging verbosity | `info` | `debug`, `info`, `warning`, `error` |
| `RELOAD` | Auto-reload on code changes | `false` (prod) / `true` (dev) | `true`, `false` |

**Examples:**

```bash
# High-performance setup
docker run -d -p 8000:8000 \
  -e WORKERS=8 \
  -e LOG_LEVEL=warning \
  spydisec/anzplus-ofx-converter:latest

# Debug mode
docker run -d -p 8000:8000 \
  -e LOG_LEVEL=debug \
  -e WORKERS=1 \
  spydisec/anzplus-ofx-converter:latest
```

## 🔄 Docker Compose

**Create `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  anzplus-ofx-converter:
    image: spydisec/anzplus-ofx-converter:latest
    container_name: anzplus-ofx-converter
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - PORT=8000
      - WORKERS=4
      - LOG_LEVEL=info
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Run:**

```bash
docker-compose up -d
```

**Included file:** [docker-compose.yml](docker-compose.yml)

## 🌍 Multi-Architecture Support

### Supported Platforms

- **linux/amd64** - Intel/AMD x86_64 processors
  - Cloud providers (AWS, GCP, Azure)
  - Desktop/laptop PCs
  - Traditional servers

- **linux/arm64** - ARM 64-bit processors
  - Apple Silicon (M1, M2, M3)
  - AWS Graviton instances
  - Raspberry Pi 4+
  - ARM-based cloud servers

### Pull Multi-Arch Image

Docker automatically pulls the correct architecture:

```bash
# On x86_64 machine → pulls linux/amd64
# On Apple Silicon → pulls linux/arm64
docker pull spydisec/anzplus-ofx-converter:latest
```

### Verify Architecture

```bash
docker image inspect spydisec/anzplus-ofx-converter:latest | grep Architecture
```

## 🚀 Deployment

### Automated Deployment via GitHub Actions

Official images are automatically built and published when maintainers create version tags:

```bash
# Maintainer workflow (automated)
git tag v1.0.0
git push origin v1.0.0
# → GitHub Actions builds multi-arch image
# → Pushes to Docker Hub as 1.0.0 and latest
```

**What happens automatically:**
1. ✅ Runs tests with pytest
2. ✅ Builds multi-arch image (amd64 + arm64)
3. ✅ Pushes to Docker Hub with tags: `1.0.0`, `latest`
4. ✅ Creates GitHub Release

**Workflow file:** [.github/workflows/docker-publish.yml](../.github/workflows/docker-publish.yml)

### Version Tags

Use specific versions for stability:

```bash
# Latest (recommended for most users)
docker pull spydisec/anzplus-ofx-converter:latest

# Pin to specific version (recommended for production)
docker pull spydisec/anzplus-ofx-converter:1.0.0
```

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use**

```bash
# Find conflicting container
docker ps | grep 8000
docker stop <container_id>

# Or use different port
docker run -d -p 8080:8000 spydisec/anzplus-ofx-converter:latest
```

**Health Check Failing**

```bash
# Check container logs
docker logs <container_name>

# Test health endpoint
curl http://localhost:8000/health

# Or inside container
docker exec <container_name> wget -O- http://localhost:8000/health
```

**Container Won't Start**

```bash
# Check logs for errors
docker logs <container_name>

# Run interactively to see errors
docker run -it -p 8000:8000 spydisec/anzplus-ofx-converter:latest

# Check Docker daemon
docker version
```

**Windows PowerShell Script Execution**

```powershell
# Allow script execution for current session
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Then run the script
.\docker\build-local.ps1
```

### Getting Help

- **Issues:** https://github.com/spydisec/PDFtoOFX/issues
- **Main README:** [../README.md](../README.md)
- **Docker Hub:** https://hub.docker.com/r/spydisec/anzplus-ofx-converter

## 📚 Additional Resources

- **Main Documentation:** [../README.md](../README.md)
- **Architecture:** [../ARCHITECTURE.md](../ARCHITECTURE.md)
- **Installation Guide:** [../INSTALLATION.md](../INSTALLATION.md)
- **GitHub Repository:** https://github.com/spydisec/PDFtoOFX

## 📄 Files in This Directory

| File | Description |
|------|-------------|
| `Dockerfile` | Multi-stage Docker image definition (Python 3.14 Alpine) |
| `docker-compose.yml` | Docker Compose configuration for local deployment |
| `build-local.ps1` | Simple PowerShell script to build locally |
| `README.md` | This file - Docker usage documentation |

## 🔐 Security

The Docker image is built with security best practices:

- ✅ **Non-root user** - Runs as `appuser` (UID 1000)
- ✅ **Minimal base** - Python 3.14 Alpine Linux (~80-120MB)
- ✅ **Updated packages** - `apk upgrade` in both build stages
- ✅ **No secrets** - Stateless, no persistent data
- ✅ **Health checks** - Automated container health monitoring
- ✅ **Multi-stage build** - Only runtime dependencies in final image

---

**Docker Hub:** https://hub.docker.com/r/spydisec/anzplus-ofx-converter  
**GitHub:** https://github.com/spydisec/PDFtoOFX
