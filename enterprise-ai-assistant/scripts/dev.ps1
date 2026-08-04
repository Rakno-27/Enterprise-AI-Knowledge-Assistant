# PowerShell Development Launch Script for Enterprise AI Assistant
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Starting Enterprise AI Assistant System" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Start Backend
Write-Host "[1/2] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m uvicorn app.main:app --reload --port 8000"

# Start Frontend
Write-Host "[2/2] Starting Next.js Frontend on http://localhost:3000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "Services started! Open http://localhost:3000 in your browser." -ForegroundColor Yellow
