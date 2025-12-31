@echo off
REM Build Sphinx documentation for PandaPOS Team52

echo Building HTML documentation...
cd /d "%~dp0"
call make.bat html

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Documentation built successfully!
    echo ========================================
    echo.
    echo To view the documentation, open:
    echo %~dp0_build\html\index.html
    echo.
    pause
) else (
    echo.
    echo ========================================
    echo Build failed! Check the errors above.
    echo ========================================
    echo.
    pause
)
