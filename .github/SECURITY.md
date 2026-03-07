# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

Please report security vulnerabilities by creating a [Security Advisory](https://github.com/spydisec/PDFtoOFX/security/advisories/new).

**Do NOT create public GitHub issues for security vulnerabilities.**

### What to include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline:
- **Initial response:** Within 48 hours
- **Status update:** Within 7 days
- **Fix timeline:** Depends on severity
  - Critical: 24-48 hours
  - High: 7 days
  - Medium: 30 days
  - Low: Best effort

## Security Measures

This project implements the following security measures:

### Build & Dependencies
- ✅ **Hash-pinned dependencies** - All Python packages with SHA256 cryptographic verification
- ✅ **Supply chain protection** - pip-tools workflow prevents dependency tampering
- ✅ **Reproducible builds** - Lockfile (`requirements.txt`) ensures identical dependency versions
- ✅ **Platform-specific optimization** - Production builds exclude development dependencies (no watchfiles)
- ✅ **Dependabot alerts** - Automated dependency vulnerability scanning (GitHub Actions, Docker only)
- ✅ **CodeQL analysis** - Static code security scanning
- ✅ **Weekly security updates** - Automated GitHub Actions and Docker base image updates

### Docker Image
- ✅ **Non-root user** - Containers run as unprivileged user (UID 1000)
- ✅ **Minimal Alpine base** - Reduced attack surface (~80-120MB)
- ✅ **Pinned Alpine version** - `python:3.14-alpine3.21` (allows Python patch updates for security fixes)
- ✅ **Multi-stage builds** - Build dependencies separated from runtime
- ✅ **No secrets in image** - Stateless design
- ✅ **Multi-arch support** - linux/amd64, linux/arm64
- ✅ **Docker Hub scanning** - Automated security scanning

### Application Security
- ✅ **Path traversal protection** - Strict filename validation (CWE-22)
- ✅ **Cryptographically secure filenames** - OFX downloads use `secrets.token_hex(6)` for 12-char random suffix
- ✅ **No data persistence** - Files processed in-memory only
- ✅ **Temporary file cleanup** - Auto-deletion after processing
- ✅ **Input validation** - PDF file type verification
- ✅ **Health checks** - Container health monitoring
- ✅ **Secure file handling** - Path resolution and symlink protection

### CI/CD
- ✅ **GitHub Actions security** - Minimal permissions, secure workflows
- ✅ **Automated testing** - pytest test suite on every build
- ✅ **Version pinning** - Exact version tags for reproducibility
- ✅ **Multi-arch builds** - Consistent builds across platforms

## Known Limitations

- Web interface has no authentication (designed for local/trusted network use)
- No rate limiting (deploy behind reverse proxy for production)
- File uploads limited to PDF only (by design)
- Temporary files stored in system temp directory (1 hour TTL)

## Security Updates

Security updates are released as patch versions (e.g., v1.0.1, v1.0.2).

Subscribe to:
- [GitHub Security Advisories](https://github.com/spydisec/PDFtoOFX/security/advisories)
- [GitHub Releases](https://github.com/spydisec/PDFtoOFX/releases)

## Recent Security Fixes
5)
- **Fixed:** OFX filename generation now uses cryptographically secure random suffix (`secrets.token_hex(6)`)
- **Added:** Hash-pinned dependencies with SHA256 verification (1200+ hashes)
- **Added:** pip-tools workflow for supply chain protection
- **Changed:** Alpine base image allows Python patch updates for security fixes
- **Optimized:** Removed watchfiles dependency (Rust-compiled, dev-only) from production builds
- **Enhanced:** Platform-specific uvicorn configuration for Windows vs Linux/Docker

### v1.0.0 (Previous)
- **Fixed:** Path traversal vulnerability (CWE-22) in file download endpoint
- **Added:** Strict filename validation with pattern matching
- **Added:** Path resolution checks to prevent symlink attacks
- **Added:** Security documentation and policies

## Dependency Security

### Hash Verification

All Python dependencies in `requirements.txt` include SHA256 hashes for cryptographic verification:

```python
# Example from requirements.txt
pandas==2.3.3 \
    --hash=sha256:0242fe9a49aa8b4d78a4fa03acb397a58833ef6199e9aa40a95f027bb3a1b6e7 \
    --hash=sha256:1611aedd912e1ff81ff41c745822980c49ce4a7907537be8692c8dbc31924593
```

**Security Benefits:**
- **Supply Chain Attack Prevention:** pip verifies package integrity before installation
- **Reproducible Builds:** Exact same dependencies across all environments
- **Tamper Detection:** Build fails if any package hash doesn't match

### Dependency Update Workflow

Manual updates using pip-tools ensure security review:

```powershell
# 1. Update requirements.in with new version
# 2. Regenerate hashes
pip-compile --generate-hashes requirements.in

# 3. Test Docker build
.\docker\build-local.ps1

# 4. Review changes and commit
git diff requirements.txt
git commit -m "deps: Upgrade package X to Y.Z"
```

**Note:** Dependabot is disabled for pip ecosystem to avoid conflicts with hash-pinned requirements. GitHub Actions and Docker base images receive automated updates.ymlink attacks
- **Added:** Security documentation and policies

## Vulnerability Disclosure Policy

We follow responsible disclosure:

1. **Report received** - Acknowledged within 48 hours
2. **Investigation** - Validate and assess impact
3. **Fix development** - Create patch in private fork
4. **Security advisory** - Draft GitHub Security Advisory
5. **Coordinated release** - Patch released with advisory
6. **Public disclosure** - 90 days after fix or coordinated disclosure

## Security Best Practices for Deployment

When deploying this application:

1. **Use HTTPS** - Always deploy behind HTTPS reverse proxy (nginx, Caddy, Traefik)
2. **Network isolation** - Deploy on trusted networks or use authentication proxy
3. **Rate limiting** - Implement rate limiting at reverse proxy level
4. **File size limits** - Configure reverse proxy to enforce upload limits
5. **Monitoring** - Enable logging and monitoring for security events
6. **Regular updates** - Keep Docker images and dependencies updated
7. **Firewall rules** - Restrict network access to necessary ports only

## Contact

- **GitHub Issues:** https://github.com/spydisec/PDFtoOFX/issues (non-security only)
- **Security Advisories:** https://github.com/spydisec/PDFtoOFX/security/advisories
- **Maintainer:** @spydisec

---

**Last Updated:** January 26, 2026
