@echo off
title Sistema de Inventario Escolar
cd /d "%~dp0"

color 0B
echo ============================================
echo   Sistema de Inventario Escolar
echo ============================================
echo.

REM Verificar que el venv existe
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] No se encuentra venv\Scripts\python.exe
    echo Ejecute: python -m venv venv
    pause
    exit /b 1
)

echo [1/3] Iniciando servidor...
start "Inventario Escolar - Servidor" ".\venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

REM Esperar a que el servidor responda
echo [2/3] Esperando al servidor...
:wait_loop
timeout /t 2 /nobreak >nul
>nul 2>&1 curl -s http://127.0.0.1:8000/ || goto wait_loop

echo [3/3] Abriendo navegador...
start http://localhost:8000

exit
