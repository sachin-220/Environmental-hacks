@echo off
echo ==========================================================
echo Starting AERIS Atmospheric Decision Intelligence System...
echo ==========================================================

start "AERIS Backend API (Port 8000)" cmd /k "python -m uvicorn api.server:app --host 127.0.0.1 --port 8000"
echo Waiting for AERIS backend to initialize models and telemetry...
timeout /t 8 /nobreak >nul
start "AERIS Frontend Dashboard (Port 3000)" cmd /k "cd dashboard && npm run dev"

echo.
echo Servers have been launched in separate windows!
echo - Frontend Dev Server:   http://localhost:3000/
echo - Production Unified SPA: http://localhost:8000/
echo - API Documentation:     http://localhost:8000/docs
echo.
pause
