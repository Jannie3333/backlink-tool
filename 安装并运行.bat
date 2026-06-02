@echo off
chcp 65001 >nul
cd /d "%~dp0"
pip install playwright openpyxl plyer >nul 2>&1
python -m playwright install chromium >nul 2>&1
python main.py
pause
