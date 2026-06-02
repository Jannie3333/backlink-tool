@echo off
chcp 65001 >nul
title 外链工具箱

echo.
echo  ============================================
echo    外链工具箱 · Pixocto.ai
echo  ============================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  ❌ 未检测到 Python，请先安装 Python 3.10+
    pause & exit /b 1
)

:: 安装依赖（首次或有更新时）
echo  [1/3] 检查并安装依赖...
pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo  ❌ 依赖安装失败
    pause & exit /b 1
)

:: 安装 Playwright 浏览器
echo  [2/3] 检查 Playwright 浏览器内核...
playwright install chromium --quiet
if %errorlevel% neq 0 (
    echo  ⚠️  Playwright 安装警告，尝试继续...
)

:: 启动 Streamlit
echo  [3/3] 启动工具（浏览器将自动打开）...
echo.
start "" http://localhost:8501
streamlit run app.py --server.port 8501 --server.headless false --browser.gatherUsageStats false

pause
