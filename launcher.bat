@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist "QQ_ai\main.py" (
    echo ???? QQ_ai\main.py...
    python "QQ_ai\main.py"
) else (
    echo ??: ??? QQ_ai\main.py
    pause
)
pause
