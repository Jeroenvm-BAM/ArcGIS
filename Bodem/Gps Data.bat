@echo off
title ArcGIS Pro - Export Field Maps Lagen Bodem
cd /d "C:\GIS"

:START
echo.
echo =====================================================
echo   Diana's Exporteer lounge van GPS data (Bodem) V1.00
echo =====================================================
echo.

set "projectnummer="

set /p projectnummer=Voer projectnummer in (bijv. COP.26xxx): 
if "%projectnummer%"=="" (
    echo.
    echo ERROR: Projectnummer mag niet leeg zijn!
    pause
    goto START
)

echo.
echo =====================================================
echo   Project: %projectnummer%
echo   Zoeken naar bijbehorende webmap en exporteren...
echo   Dit kan even duren...
echo =====================================================
echo.

"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" export_project_layers.py %projectnummer%

echo.
echo =====================================================
echo Export voltooid (check map C:\GIS\Download)
echo =====================================================
echo.
pause