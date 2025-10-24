@echo off
echo ====================================
echo 大富翁游戏启动器
echo ====================================
echo.
echo 正在检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo.
echo 正在检查Pygame...
python -c "import pygame" 2>nul
if errorlevel 1 (
    echo Pygame未安装，正在安装...
    pip install pygame
    if errorlevel 1 (
        echo 错误: Pygame安装失败
        pause
        exit /b 1
    )
)

echo.
echo 启动游戏...
echo.
python main.py

pause

