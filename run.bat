@echo off
title Amplio Services
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
  echo No venv found. Create one with: py -3 -m venv venv
  echo Then: venv\Scripts\pip install -r requirements.txt
  echo       venv\Scripts\pip install "uvicorn[standard]"
  pause
  exit /b 1
)

echo Starting app and opening your browser...
venv\Scripts\python.exe "%~dp0run.py"
pause
