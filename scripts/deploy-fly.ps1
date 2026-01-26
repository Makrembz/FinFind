# PowerShell Deployment Script for Fly.io
# FinFind Application

param(
    [Parameter(Position=0)]
    [ValidateSet("backend", "frontend", "all")]
    [string]$Target = "all"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 FinFind Deployment to Fly.io" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check if flyctl is installed
try {
    $null = Get-Command flyctl -ErrorAction Stop
} catch {
    Write-Host "❌ flyctl is not installed. Please install it first:" -ForegroundColor Red
    Write-Host "   iwr https://fly.io/install.ps1 -useb | iex" -ForegroundColor Yellow
    exit 1
}

# Check if logged in
try {
    flyctl auth whoami 2>$null | Out-Null
} catch {
    Write-Host "❌ Not logged in to Fly.io. Please run: flyctl auth login" -ForegroundColor Red
    exit 1
}

Write-Host "✅ flyctl is installed and authenticated" -ForegroundColor Green

function Deploy-Backend {
    Write-Host ""
    Write-Host "📦 Deploying Backend..." -ForegroundColor Cyan
    Write-Host "------------------------" -ForegroundColor Cyan
    
    # Check if app exists
    $apps = flyctl apps list 2>$null
    if ($apps -notmatch "finfind-backend") {
        Write-Host "Creating backend app..."
        flyctl apps create finfind-backend
    }
    
    # Set secrets
    Write-Host "Setting secrets..."
    if ($env:GROQ_API_KEY) {
        flyctl secrets set GROQ_API_KEY="$env:GROQ_API_KEY" --app finfind-backend 2>$null
    }
    if ($env:QDRANT_URL) {
        flyctl secrets set QDRANT_URL="$env:QDRANT_URL" --app finfind-backend 2>$null
    }
    if ($env:QDRANT_API_KEY) {
        flyctl secrets set QDRANT_API_KEY="$env:QDRANT_API_KEY" --app finfind-backend 2>$null
    }
    
    # Deploy
    flyctl deploy --config fly.toml --app finfind-backend
    
    Write-Host "✅ Backend deployed successfully!" -ForegroundColor Green
    Write-Host "   URL: https://finfind-backend.fly.dev" -ForegroundColor Cyan
}

function Deploy-Frontend {
    Write-Host ""
    Write-Host "🎨 Deploying Frontend..." -ForegroundColor Cyan
    Write-Host "------------------------" -ForegroundColor Cyan
    
    # Check if app exists
    $apps = flyctl apps list 2>$null
    if ($apps -notmatch "finfind-frontend") {
        Write-Host "Creating frontend app..."
        flyctl apps create finfind-frontend
    }
    
    # Deploy
    flyctl deploy --config fly.frontend.toml --app finfind-frontend
    
    Write-Host "✅ Frontend deployed successfully!" -ForegroundColor Green
    Write-Host "   URL: https://finfind-frontend.fly.dev" -ForegroundColor Cyan
}

# Execute based on target
switch ($Target) {
    "backend" { Deploy-Backend }
    "frontend" { Deploy-Frontend }
    "all" { 
        Deploy-Backend
        Deploy-Frontend
    }
}

Write-Host ""
Write-Host "🎉 Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  flyctl status --app finfind-backend    # Check backend status"
Write-Host "  flyctl logs --app finfind-backend      # View backend logs"
Write-Host "  flyctl status --app finfind-frontend   # Check frontend status"
Write-Host "  flyctl logs --app finfind-frontend     # View frontend logs"
