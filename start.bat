@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo        ReSource AI - Industrial Waste Exchange
echo         Circular Economy & AI Matching Platform
echo ========================================================
echo.

cd /d "%~dp0"

:: 1. Check/create .env
if not exist ".env" (
    echo [1/4] Creating .env from .env.example...
    copy ".env.example" ".env" >nul
) else (
    echo [1/4] .env configuration file detected.
)

:: 2. Setup Python virtual environment
echo [2/4] Checking Python backend virtual environment...
if not exist "backend\venv\Scripts\python.exe" (
    echo Creating virtual environment in backend\venv...
    where py >nul 2>&1
    if !errorlevel! equ 0 (
        py -m venv backend\venv
    ) else (
        where python >nul 2>&1
        if !errorlevel! equ 0 (
            python -m venv backend\venv
        ) else (
            echo [ERROR] Neither 'py' nor 'python' was found in your PATH. Please install Python 3.11+.
            pause
            exit /b 1
        )
    )
)

echo Installing/verifying backend dependencies...
backend\venv\Scripts\pip.exe install -r backend\requirements.txt --quiet

:: 3. Setup Frontend dependencies
echo [3/4] Checking frontend node_modules...
if not exist "frontend\node_modules" (
    echo Installing frontend packages with npm...
    cd frontend
    call npm install
    cd ..
)

:: 4. Start Backend and Frontend
echo [4/4] Starting ReSource AI Servers...
echo.
echo --------------------------------------------------------
echo  Backend API:  http://localhost:8000/docs
echo  Frontend Web: http://localhost:3000
echo --------------------------------------------------------
echo.
echo Demo Login Credentials:
echo   Supplier: supplier@demo.com  (Password: password123)
echo   Buyer:    buyer@demo.com     (Password: password123)
echo.

:: Launch Backend in separate window
start "ReSource AI - Backend (Port 8000)" cmd /k "cd /d "%~dp0backend" && set PYTHONPATH=. && venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Launch Frontend in separate window
start "ReSource AI - Frontend (Port 3000)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo Servers started! Opening browser at http://localhost:3000 in 4 seconds...
timeout /t 4 >nul
start http://localhost:3000

echo.
echo Keep both console windows open while running ReSource AI.
echo Press any key to exit this launcher window...
pause >nul
