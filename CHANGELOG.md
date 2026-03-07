# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2026-03-07

### Fixed
- Corrected sign inversion for inter-account transfers (FROM/TO keywords) in OFX output (#13)

### Security
- Bumped werkzeug 3.1.5 → 3.1.6 — fixes Windows device name path traversal (GHSA-29vq-49wr-vm6x) (#17)
- Bumped pillow 12.1.0 → 12.1.1, cryptography 46.0.3 → 46.0.5, protobuf 6.33.4 → 6.33.5 (#14)

### Changed
- CI: Fixed conventional commits check (comma-separated format) (#18)
- CI: Added workflow permissions for PR comments (#16)
- CI: Replaced unmaintained `toml` package with stdlib `tomllib` in release workflow (#16)
- CI: Docker build now triggered via `workflow_dispatch` instead of relying on tag push (#19)

## [1.1.0] - 2026-03-07

### Fixed
- Corrected sign inversion for inter-account transfers (FROM/TO keywords) in OFX output (#13)

### Security
- Bumped werkzeug 3.1.5 → 3.1.6 — fixes Windows device name path traversal (GHSA-29vq-49wr-vm6x) (#17)
- Bumped pillow 12.1.0 → 12.1.1, cryptography 46.0.3 → 46.0.5, protobuf 6.33.4 → 6.33.5 (#14)

### Changed
- CI: Fixed conventional commits check (comma-separated format) (#18)
- CI: Added workflow permissions for PR comments (#16)
- CI: Replaced unmaintained `toml` package with stdlib `tomllib` in release workflow (#16)
- CI: Docker build now triggered via `workflow_dispatch` instead of relying on tag push (#19)

## [1.0.3] - 2026-01-26

### Changed
- Simplified repository structure following KISS principle - removed unnecessary documentation files

## [1.0.2]

### Added
- Automated release workflow via GitHub Actions
- Conventional Commits enforcement for better changelog generation
- Dockerfile now automatically compiles requirements.in inside Alpine during build

### Changed
- Version bumping now automated via `workflow_dispatch` trigger
- **Simplified dependency workflow** - No manual pip-compile needed, Dockerfile handles it
- Requirements compilation moved into Dockerfile for automatic Alpine compatibility

### Removed
- Manual Alpine compilation scripts (no longer needed)

### Documentation
- Added comprehensive release process guide (.github/RELEASE_PROCESS.md)
- Added simplified dependency workflow guide (.docker-maintainer/DEPENDENCY_WORKFLOW.md)

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

[Unreleased]: https://github.com/spydisec/PDFtoOFX/compare/v1.2.1...HEAD
[1.2.1]: https://github.com/spydisec/PDFtoOFX/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/spydisec/PDFtoOFX/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/spydisec/PDFtoOFX/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/spydisec/PDFtoOFX/compare/v1.0.3...v1.1.0
[1.0.3]: https://github.com/spydisec/PDFtoOFX/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/spydisec/PDFtoOFX/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/spydisec/PDFtoOFX/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/spydisec/PDFtoOFX/releases/tag/v1.0.0
