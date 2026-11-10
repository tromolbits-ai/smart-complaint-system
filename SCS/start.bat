@echo off
title Smart Complaint System (SCS) - Kota Bandar Lampung
echo ============================================================
echo   SMART COMPLAINT SYSTEM (SCS) - KOTA BANDAR LAMPUNG
echo   Sistem Pengaduan Masyarakat Berbasis Smart City
echo ============================================================
echo.

set PYTHON_CMD=

if exist "C:\msys64\ucrt64\bin\python.exe" (
    set "PYTHON_CMD=C:\msys64\ucrt64\bin\python.exe"
    goto RUN
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PYTHON_CMD=python"
    goto RUN
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PYTHON_CMD=py"
    goto RUN
)

echo [ERROR] Python tidak ditemukan di sistem.
echo Harap pastikan Python terinstal.
pause
exit /b 1

:RUN
echo Menjalankan aplikasi dengan %PYTHON_CMD%...
"%PYTHON_CMD%" run.py
pause

