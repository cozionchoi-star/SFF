@echo off
cd /d %~dp0
set VERSION=2.1
set PYINST=C:\Users\heyzi\AppData\Local\Programs\Python\Python313\Scripts\pyinstaller.exe
set DEST=%USERPROFILE%\OneDrive - SOUTHERN TREASURE\SFF

echo --- Closing SFF if running ---
taskkill /f /im SFF.exe >nul 2>&1

echo --- Step 1: Build EXE ---
if exist dist\SFF rmdir /s /q dist\SFF
if exist dist\SFF.exe del /f /q dist\SFF.exe
if exist build rmdir /s /q build

"%PYINST%" build.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

echo --- Step 2: Deploy to OneDrive ---
copy /y "dist\SFF.exe" "%DEST%\SFF.exe"
echo %VERSION%> "%DEST%\version.txt"

echo.
echo --- Build Complete: v%VERSION% ---
echo Deployed to: %DEST%\SFF.exe
pause
