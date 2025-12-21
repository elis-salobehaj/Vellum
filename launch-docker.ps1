# Check if Docker is running
docker info | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit
}

# Check if .env exists, if not copy from example
if (!(Test-Path .env)) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "Please edit the .env file with your API keys and restart the script." -ForegroundColor Yellow
    exit
}

Write-Host "Starting kbase-ai stack..." -ForegroundColor Green
docker-compose up --build
