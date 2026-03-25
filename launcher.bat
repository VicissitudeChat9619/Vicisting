@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist "QQ_ai\main.py" (
    echo 正在运行 QQ_ai\main.py...
    python "QQ_ai\main.py"
) else (
    echo 错误: 找不到 QQ_ai\main.py
    pause
)
