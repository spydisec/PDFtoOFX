#!/usr/bin/env pwsh
# Simple local Docker build script

$ErrorActionPreference = "Stop"

Write-Host "`n=== Building Docker Image Locally ===" -ForegroundColor Cyan

# Build from project root
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "`nBuilding anzplus-ofx:local..." -ForegroundColor Yellow
docker build -f docker/Dockerfile -t anzplus-ofx:local .

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Build completed successfully!" -ForegroundColor Green
    Write-Host "Image: anzplus-ofx:local`n" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Build failed!" -ForegroundColor Red
    exit 1
}
