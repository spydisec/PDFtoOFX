# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Automated release workflow via GitHub Actions
- Conventional Commits enforcement for better changelog generation
- Alpine-native dependency compilation scripts (`compile-requirements.ps1` and `.sh`)

### Changed
- Version bumping now automated via `workflow_dispatch` trigger
- **BREAKING:** `requirements.txt` must now be generated inside Alpine Docker container
- Dependency workflow updated to use Docker-based pip-compile for Alpine compatibility

### Documentation
- Added comprehensive release process guide (.github/RELEASE_PROCESS.md)
- Documented "Golden Rule" for Alpine dependency generation

## [1.0.1] - 2025-01-26

### Security
- Improved OFX filename generation with cryptographically secure random suffix using `secrets.token_hex(6)`
- Implemented hash-pinned dependencies with SHA256 verification for supply chain security
- All dependencies now require cryptographic verification during installation

### Changed
- Updated Alpine base image from `python:3.14.0-alpine3.21` to `python:3.14-alpine3.21` to allow Python patch updates
- Migrated dependency management from manual `requirements.txt` to pip-tools workflow
- Split requirements into `requirements.in` (source) and `requirements.txt` (hash-pinned lockfile)
- Optimized uvicorn configuration: removed `uvicorn[standard]` to eliminate Rust-compiled `watchfiles` (dev-only dependency)
- Added platform-specific dependencies using `sys_platform` markers for Windows vs Linux/Docker compatibility

### Performance
- Reduced Docker image size by removing unnecessary development dependencies
- Faster Docker builds without Rust/Cargo compilation (no `watchfiles`)
- Maintained uvicorn performance with manual `uvloop` and `httptools` on Linux

### Documentation
- Added CHANGELOG.md following Keep a Changelog format
- Configured Release Drafter for automated release note generation
- Updated SECURITY.md with hash pinning details
- Enhanced .docker-maintainer/README.md with pip-tools workflow

## [1.0.0] - 2024-XX-XX

### Added
- Initial release of PDFtoOFX converter
- ANZ Plus bank statement PDF parsing
- OFX (Open Financial Exchange) format generation
- Docker containerization with Alpine Linux
- FastAPI web interface
- Command-line conversion tool

[Unreleased]: https://github.com/yourusername/PDFtoOFX/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/yourusername/PDFtoOFX/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/yourusername/PDFtoOFX/releases/tag/v1.0.0
