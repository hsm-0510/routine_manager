@echo off
setlocal

REM Build the Weighbridge System EXE using PyInstaller
REM Run this from the project root: routine_manager\

cd /d "%~dp0"

echo ========================================
echo   Building WeighbridgeSystem.exe
echo ========================================
echo.

REM Ensure PyInstaller is available
python -m PyInstaller --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo PyInstaller not found. Installing...
    python -m pip install --upgrade pip >nul 2>&1
    python -m pip install pyinstaller >nul 2>&1
)

echo Cleaning previous builds...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo Building EXE...
python -m PyInstaller ^
  --onefile ^
  --name "WeighbridgeSystem" ^
  --add-data "config;config" ^
  --add-data "dashboard;dashboard" ^
  --add-data "sample;sample" ^
  --add-data "tests;tests" ^
  --add-data "docs;docs" ^
  --add-data "image;image" ^
  --add-data "requirements.txt;." ^
  --add-data "routine_manager.bat;." ^
  --hidden-import tests.test7_sap_opc ^
  --hidden-import sample.inferenceEngineML.prediction ^
  main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   Build completed successfully!
    echo ========================================
    echo.
    echo Output: %cd%\dist\WeighbridgeSystem.exe
    echo.
    start "" "%cd%\dist"
) else (
    echo.
    echo Build failed with error code %ERRORLEVEL%
    pause
)

endlocal
