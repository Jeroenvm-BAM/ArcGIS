@echo off
title ArcGIS Pro - Nieuw Field Maps Project
cd /d "C:\GIS"

:: Dwing Python om ALLE waarschuwingen overal te negeren
set PYTHONWARNINGS=ignore

:START
echo.
echo =====================================================
echo   Nieuw Field Maps Project Bodem aanmaken V1.00
echo =====================================================
echo.

set "projectnummer="
set "projectnaam="

set /p projectnummer=Voer projectnummer in (bijv. COP.26xxx): 
if "%projectnummer%"=="" (
    echo.
    echo ERROR: Projectnummer mag niet leeg zijn!
    pause
    goto START
)

set /p projectnaam=Voer projectnaam in (bijv. plaatsnaam of projectnaam): 
if "%projectnaam%"=="" (
    echo.
    echo ERROR: Projectnaam mag niet leeg zijn!
    pause
    goto START
)

echo.
echo =====================================================
echo   Project: %projectnummer% - %projectnaam%
echo   Script wordt gestart... Neem een bak koffie in de tussentijd...
echo =====================================================
echo.

"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" run_project_tool_bodem.py %projectnummer% "%projectnaam%" 2>nul

echo.
echo =====================================================
echo Script voltooid.
echo =====================================================
echo.
pause