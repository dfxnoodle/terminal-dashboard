@echo off
REM Terminal Dashboard Development Server Starter
REM Usage: start-dev.bat [frontend_port] [backend_port]
REM Example: start-dev.bat 3000 8000

echo Starting Terminal Dashboard Development Servers...
echo.

REM Set default ports
set FRONTEND_PORT=5173
set BACKEND_PORT=8003

REM Override ports if arguments provided
if not "%1"=="" set FRONTEND_PORT=%1
if not "%2"=="" set BACKEND_PORT=%2

echo Configuration:
echo   Frontend Port: %FRONTEND_PORT%
echo   Backend Port:  %BACKEND_PORT%
echo.

REM Start frontend in a new window
start "Frontend Dev Server (Port %FRONTEND_PORT%)" cmd /k "cd /d %~dp0frontend && npm run dev -- --port %FRONTEND_PORT%"

REM Wait a moment for the first window to open
timeout /t 2 /nobreak > nul

REM Start backend in a new window
start "Backend API Server (Port %BACKEND_PORT%)" cmd /k "cd /d %~dp0backend && uv run uvicorn main:app --reload --host 0.0.0.0 --port %BACKEND_PORT%"

echo.
echo ========================================
echo Development servers are starting...
echo ========================================
echo Frontend: http://localhost:%FRONTEND_PORT%
echo Backend:  http://localhost:%BACKEND_PORT%
echo ========================================
echo.
echo Both servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
echo Usage: start-dev.bat [frontend_port] [backend_port]
echo Example: start-dev.bat 3000 8000
echo.
pause
