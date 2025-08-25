@echo off
chcp 65001 >nul
title 智能作文评价系统启动器

echo.
echo =================================================================
echo 🌟 智能作文评价系统启动器
echo =================================================================
echo.

echo 🚀 正在启动系统...
echo 📍 工作目录: %CD%
echo.

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python环境
    echo 💡 请确保Python已正确安装并添加到PATH环境变量
    pause
    exit /b 1
)

REM 检查必要文件
if not exist "start_system.py" (
    echo ❌ 错误: 找不到start_system.py文件
    echo 💡 请确保在项目根目录下运行此脚本
    pause
    exit /b 1
)

if not exist "main.py" (
    echo ❌ 错误: 找不到main.py文件
    pause
    exit /b 1
)

if not exist "reports_server.py" (
    echo ❌ 错误: 找不到reports_server.py文件
    pause
    exit /b 1
)

echo ✅ 环境检查通过
echo.

REM 启动系统
echo 🚀 启动智能作文评价系统...
echo 💡 启动后请访问: http://127.0.0.1:8080
echo 📁 文件服务地址: http://127.0.0.1:8081
echo.
echo ⚠️  按 Ctrl+C 可停止系统
echo.

python start_system.py

echo.
echo 📢 系统已停止运行
pause