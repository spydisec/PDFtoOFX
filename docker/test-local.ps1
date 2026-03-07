#!/usr/bin/env pwsh
# Simple local container test for maintainers

$ErrorActionPreference = "Stop"

Write-Host "`n=== Testing Local Docker Image ===" -ForegroundColor Cyan

# Check if image exists
Write-Host "`nChecking if anzplus-ofx:local image exists..." -ForegroundColor Yellow
$imageExists = docker images -q anzplus-ofx:local
if (-not $imageExists) {
    Write-Host "❌ Image 'anzplus-ofx:local' not found!" -ForegroundColor Red
    Write-Host "Please run .\docker\build-local.ps1 first to build the image.`n" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Image found" -ForegroundColor Green

# Stop any existing test container
Write-Host "`nCleaning up any existing test containers..." -ForegroundColor Yellow
$existingContainer = docker ps -a -q -f name=anzplus-ofx-test
if ($existingContainer) {
    docker stop anzplus-ofx-test 2>&1 | Out-Null
    docker rm anzplus-ofx-test 2>&1 | Out-Null
    Write-Host "Removed existing container" -ForegroundColor Gray
}

# Run container
Write-Host "`nStarting test container..." -ForegroundColor Yellow
docker run -d `
    --name anzplus-ofx-test `
    -p 8888:8000 `
    -e ENVIRONMENT=development `
    anzplus-ofx:local

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Failed to start container" -ForegroundColor Red
    exit 1
}

# Wait for container to be ready
Write-Host "`nWaiting for container to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if container is running
$running = docker inspect --format='{{.State.Running}}' anzplus-ofx-test 2>&1
if ($running -ne "true") {
    Write-Host "❌ Container failed to start" -ForegroundColor Red
    Write-Host "`nContainer logs:" -ForegroundColor Yellow
    docker logs anzplus-ofx-test
    docker rm anzplus-ofx-test 2>&1 | Out-Null
    exit 1
}

# Wait for health check (up to 30 seconds)
Write-Host "Waiting for health check..." -ForegroundColor Yellow
for ($i = 1; $i -le 10; $i++) {
    Start-Sleep -Seconds 3
    $health = docker inspect --format='{{.State.Health.Status}}' anzplus-ofx-test 2>&1
    Write-Host "  Attempt $i/10: $health"
    if ($health -eq "healthy") {
        Write-Host "✅ Container is healthy" -ForegroundColor Green
        break
    }
    if ($i -eq 10) {
        Write-Host "⚠️ Health check timeout - continuing with endpoint tests..." -ForegroundColor Yellow
    }
}

# Test health endpoint
Write-Host "`nTesting /health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8888/health" -Method Get
    Write-Host "  Status: $($response.status)" -ForegroundColor Green
    Write-Host "  Service: $($response.service)" -ForegroundColor Green
    Write-Host "  Version: $($response.version)" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Health check failed: $_" -ForegroundColor Red
    docker logs anzplus-ofx-test
    docker stop anzplus-ofx-test
    docker rm anzplus-ofx-test
    exit 1
}

# Test web interface
Write-Host "`nTesting web interface..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8888/" -Method Get -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✅ Web interface accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "  ❌ Web interface failed: $_" -ForegroundColor Red
}

# Show logs
Write-Host "`nContainer logs:" -ForegroundColor Yellow
docker logs anzplus-ofx-test --tail 20

# Cleanup
Write-Host "`nCleaning up..." -ForegroundColor Yellow
docker stop anzplus-ofx-test 2>&1 | Out-Null
docker rm anzplus-ofx-test 2>&1 | Out-Null

Write-Host "`n✅ Local test completed successfully!" -ForegroundColor Green
Write-Host "Container is ready for tagging and deployment.`n" -ForegroundColor Cyan
