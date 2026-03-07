# Docker Maintenance Guide

Workflow for testing, building, and releasing the Docker image.

## Quick Release Workflow

```
1. Test locally     →  python run_web.py
2. Build Docker     →  .\docker\build-local.ps1
3. Test Docker      →  .\docker\test-local.ps1
4. Commit & push    →  git commit -m "fix: description" && git push origin main
5. Release          →  Run "Create Release" workflow in GitHub Actions UI
```

Release workflow automatically:
- Bumps version in `pyproject.toml`, `app/__init__.py`, `docker/Dockerfile`
- Updates `CHANGELOG.md`
- Creates git tag + GitHub Release
- Triggers Docker build & push to Docker Hub

## Local Testing

### 1. Test Python directly

```powershell
python run_web.py
# Visit http://localhost:8000
```

### 2. Build & test Docker image

```powershell
# Build local image
.\docker\build-local.ps1

# Run automated container tests (port 8888)
.\docker\test-local.ps1
```

The test script checks: image exists, container starts, health endpoint responds, web UI loads, then cleans up.

## CI/CD Workflows

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| `ci.yml` | Push/PR to `main` (code changes) | Runs pytest |
| `docker-publish.yml` | Push to `main` (app changes) | Builds & pushes `:main` tag |
| `docker-publish.yml` | Version tag `v*.*.*` or dispatch | Builds & pushes `:X.Y.Z` + `:latest` |
| `release.yml` | Manual dispatch | Bumps version, tags, triggers Docker build |
| `conventional-commits.yml` | Pull requests | Enforces commit message format |

## Commit Message Format

All commits **must** follow [Conventional Commits](https://www.conventionalcommits.org/) format or CI will reject the PR.

```
<type>: <description>
```

| Type | When to use | Example |
|------|-------------|---------|
| `feat` | New feature | `feat: add merchant category codes` |
| `fix` | Bug fix | `fix: correct date parsing logic` |
| `docs` | Documentation only | `docs: update README` |
| `chore` | Maintenance, deps, versions | `chore: update dependencies` |
| `refactor` | Code restructuring | `refactor: simplify PDF extraction` |
| `perf` | Performance improvement | `perf: optimize transaction parsing` |
| `test` | Add/update tests | `test: add edge case for amounts` |
| `build` | Build system changes | `build: update Docker base image` |
| `ci` | CI/CD changes | `ci: add security scanning` |
| `style` | Code formatting | `style: format with black` |
| `revert` | Revert previous commit | `revert: undo feature X` |

### Fixing bad commit messages

**Amend last commit:**
```powershell
git commit --amend -m "fix: proper description"
git push --force origin your-branch
```

**Reword older commits (advanced):**
```powershell
git rebase -i HEAD~3  # Change 'pick' to 'reword' for bad commits
git push --force origin your-branch
```

Do **not** force-push to `main` if others are working on the repo.

## AI Prompt Template

When using AI assistants for changes:

```
Project: PDFtoOFX (ANZ Plus PDF → OFX converter)
Stack: Python 3.11+, FastAPI, Docker Alpine
Deps: requirements.in (source) → requirements.txt (auto-compiled in Docker)
Tests: pytest in tests/

Task: [DESCRIBE CHANGE]

Workflow:
1. Make code changes
2. Test: python run_web.py
3. Run tests: pytest tests/ -v
4. Build Docker: .\docker\build-local.ps1
5. Test Docker: .\docker\test-local.ps1
6. Update CHANGELOG.md
7. Commit: git commit -m "<type>: <description>"
```

## Verification Links

- **GitHub Actions:** https://github.com/spydisec/PDFtoOFX/actions
- **Docker Hub:** https://hub.docker.com/r/spydisec/anzplus-ofx-converter/tags

```powershell
# Test a published image
docker pull spydisec/anzplus-ofx-converter:latest
docker run -d -p 9000:8000 spydisec/anzplus-ofx-converter:latest
# Visit http://localhost:9000
```

## Dependencies

Edit `requirements.in`, then build Docker (auto-compiles inside Alpine):

```powershell
code requirements.in    # Edit source file
.\docker\build-local.ps1  # Rebuilds requirements.txt inside Alpine
.\docker\test-local.ps1   # Verify
```

Do **not** run `pip-compile` locally — always compile inside Docker for Alpine compatibility.
