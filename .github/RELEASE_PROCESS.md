# Release Process Guide

This document explains how to create releases for the PDFtoOFX project using our automated CI/CD pipeline.

## 🚀 Quick Start: Creating a Release

### Option 1: Automated Release (Recommended)

1. **Go to GitHub Actions**
   ```
   https://github.com/spydisec/PDFtoOFX/actions/workflows/release.yml
   ```

2. **Click "Run workflow"**
   - Choose branch: `main`
   - Select version bump type:
     - `patch`: Bug fixes (1.0.1 → 1.0.2)
     - `minor`: New features (1.0.2 → 1.1.0)
     - `major`: Breaking changes (1.1.0 → 2.0.0)
   - Optional: Add release description

3. **Wait for automation**
   - ✅ Version bumped in `pyproject.toml`
   - ✅ CHANGELOG.md updated with date
   - ✅ Git commit created
   - ✅ Git tag pushed (e.g., `v1.0.2`)
   - ✅ GitHub Release created with notes
   - ✅ Docker build triggered automatically

### Option 2: Manual Release (Advanced)

If you prefer manual control:

```powershell
# 1. Update version in pyproject.toml
code pyproject.toml
# Change: version = "1.0.1" → version = "1.0.2"

# 2. Update CHANGELOG.md
code CHANGELOG.md
# Replace: ## [Unreleased]
# With:    ## [Unreleased]
#          
#          ## [1.0.2] - 2025-01-26

# 3. Commit changes
git add pyproject.toml CHANGELOG.md
git commit -m "chore: Release v1.0.2"
git push origin main

# 4. Create tag
git tag -a v1.0.2 -m "Release v1.0.2

Brief description of changes"
git push origin v1.0.2

# 5. Docker build triggers automatically on tag push
```

## 📝 Before Creating a Release

### 1. Update CHANGELOG.md

Move your changes from `[Unreleased]` section to a new version section:

```markdown
## [Unreleased]

## [1.0.2] - 2025-01-26

### Fixed
- Corrected MEMO field handling for transactions over 200 characters

### Changed
- Updated pandas to 2.4.0
```

### 2. If You Updated Dependencies

**IMPORTANT:** Always regenerate `requirements.txt` inside Alpine Docker container:

```powershell
# After editing requirements.in
.\.docker-maintainer\compile-requirements.ps1

# Test the build
.\docker\build-local.ps1
```

**Why?** pip-compile on Windows/macOS may select incompatible wheels that fail on Alpine Linux.

### 2. Use Conventional Commits

We enforce [Conventional Commits](https://www.conventionalcommits.org/) for clear changelog generation:

```bash
# Features
git commit -m "feat: Add support for Westpac bank statements"

# Bug fixes
git commit -m "fix: Correct date parsing for leap years"

# Documentation
git commit -m "docs: Update Docker installation guide"

# Chores
git commit -m "chore: Upgrade dependencies"

# Performance
git commit -m "perf: Optimize PDF parsing with caching"

# Breaking changes
git commit -m "feat!: Change API endpoint structure

BREAKING CHANGE: /convert endpoint moved to /api/v2/convert"
```

**Commit Types:**
- `feat:` - New feature (bumps **minor** version)
- `fix:` - Bug fix (bumps **patch** version)
- `docs:` - Documentation
- `chore:` - Maintenance
- `style:` - Code formatting
- `refactor:` - Code restructuring
- `perf:` - Performance improvement
- `test:` - Test changes
- `build:` - Build system
- `ci:` - CI/CD changes
- `revert:` - Revert commit
- `!` suffix - Breaking change (bumps **major** version)

## 🔄 Release Workflow Details

### What Happens Automatically

When you run the release workflow or push a tag:

1. **Version Bump** (if using workflow)
   - Reads current version from `pyproject.toml`
   - Calculates new version based on bump type
   - Updates `pyproject.toml` with new version

2. **CHANGELOG Update** (if using workflow)
   - Replaces `[Unreleased]` with new version and date
   - Updates version comparison links
   - Preserves changelog history

3. **Git Operations**
   - Commits version changes
   - Creates annotated git tag
   - Pushes to `main` branch

4. **GitHub Release**
   - Extracts relevant section from CHANGELOG
   - Creates GitHub Release with notes
   - Attaches release assets (if any)

5. **Docker Build** (triggered by tag)
   - Builds multi-arch images (amd64, arm64)
   - Pushes to Docker Hub with tags:
     - `latest`
     - `v1.0.2`
     - `v1.0`
     - `v1`

### Version Bump Strategy

```
Current: 1.2.3

patch:  1.2.3 → 1.2.4  (Bug fixes, minor changes)
minor:  1.2.3 → 1.3.0  (New features, backwards compatible)
major:  1.2.3 → 2.0.0  (Breaking changes)
```

## 📋 CHANGELOG.md Format

We follow [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [Unreleased]

### Added
- New features go here

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security improvements

## [1.0.2] - 2025-01-26

### Fixed
- Bug fix description
```

## 🎯 Examples

### Example 1: Patch Release (Bug Fix)

**Scenario:** Fixed a bug in PDF parsing

```markdown
# 1. Update CHANGELOG.md
## [Unreleased]

### Fixed
- Corrected date parsing for ANZ Plus statements in leap years

# 2. Run GitHub Actions workflow
- Version bump: patch (1.0.1 → 1.0.2)
- Description: "Fixed leap year date parsing bug"

# 3. Result
- pyproject.toml: version = "1.0.2"
- Git tag: v1.0.2
- Docker Hub: spydisec/anzplus-ofx-converter:1.0.2
```

### Example 2: Minor Release (New Feature)

**Scenario:** Added support for another bank

```markdown
# 1. Update CHANGELOG.md
## [Unreleased]

### Added
- Support for Westpac bank statement PDFs
- New parser: `westpac_parser.py`

# 2. Run GitHub Actions workflow
- Version bump: minor (1.0.2 → 1.1.0)
- Description: "Added Westpac bank support"

# 3. Result
- pyproject.toml: version = "1.1.0"
- Git tag: v1.1.0
- Docker Hub: spydisec/anzplus-ofx-converter:1.1.0
```

### Example 3: Major Release (Breaking Change)

**Scenario:** Changed API structure

```markdown
# 1. Update CHANGELOG.md
## [Unreleased]

### Changed
- **BREAKING:** Moved all endpoints to /api/v2/ prefix
- Updated Docker health check endpoint

### Migration Guide
- Old: POST /upload → New: POST /api/v2/upload
- Old: GET /download → New: GET /api/v2/download

# 2. Run GitHub Actions workflow
- Version bump: major (1.1.0 → 2.0.0)
- Description: "API v2 - Breaking changes"

# 3. Result
- pyproject.toml: version = "2.0.0"
- Git tag: v2.0.0
- Docker Hub: spydisec/anzplus-ofx-converter:2.0.0
```

## 🔧 Troubleshooting

### Release Workflow Failed

**Check GitHub Actions logs:**
```
https://github.com/spydisec/PDFtoOFX/actions
```

**Common issues:**
- CHANGELOG.md syntax error - Ensure proper Markdown format
- pyproject.toml parse error - Validate TOML syntax
- Git conflicts - Pull latest changes before releasing

### Docker Build Not Triggered

**Verify tag was pushed:**
```powershell
git ls-remote --tags origin
```

**Manually trigger Docker build:**
```
https://github.com/spydisec/PDFtoOFX/actions/workflows/docker-build.yml
```

### Wrong Version Number

**Delete tag and retry:**
```powershell
# Delete local tag
git tag -d v1.0.2

# Delete remote tag
git push origin :refs/tags/v1.0.2

# Delete GitHub Release (via GitHub UI)

# Retry release workflow
```

## 📚 References

- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Actions](https://docs.github.com/en/actions)

## 🆘 Need Help?

- **GitHub Issues:** https://github.com/spydisec/PDFtoOFX/issues
- **Discussions:** https://github.com/spydisec/PDFtoOFX/discussions
- **Maintainer:** @spydisec
