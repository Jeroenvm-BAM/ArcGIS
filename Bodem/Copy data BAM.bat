@echo off
setlocal EnableDelayedExpansion

title Kopieer BAM GIS software - zoeken op stick-naam "USB-C Stick"

echo.
echo ==============================================
echo   Zoeken naar USB-stick met naam "USB-C Stick"
echo   en kopiëren van BAM\Software\GIS naar C:\GIS
echo ==============================================
echo.

set "STICK_NAAM=USB-C Stick"

set "SOURCE="
for /f "tokens=1,2 delims==" %%a in ('wmic volume get DriveLetter^, Label ^| find /i "%STICK_NAAM%"') do (
    if /i "%%b"=="%STICK_NAAM%" (
        set "DRIVE=%%a"
        set "SOURCE=!DRIVE!:\BAM\Software\GIS"
        goto :gevonden
    )
)

echo.
echo FOUT: Geen USB-stick gevonden met naam "%STICK_NAAM%"
echo.
echo Controleer het volgende:
echo  • Is de stick aangesloten?
echo  • Staat de naam in Verkenner precies "USB-C Stick"? (rechtsklik → Eigenschappen → naam bovenaan)
echo  • Soms staat er een spatie extra of hoofdletters anders
echo.
pause
exit /b 1

:gevonden
:: Verwijder eventuele spaties rond de drive letter
set SOURCE=%SOURCE: =%

if not exist "%SOURCE%" (
    echo FOUT: Map BAM\Software\GIS niet gevonden op %DRIVE%:\
    echo Controleer of de mapstructuur klopt: %DRIVE%:\BAM\Software\GIS
    pause
    exit /b 1
)

echo Gevonden op %SOURCE%

:: Ga naar C:\
C:

:: Maak map C:\GIS aan als die er nog niet is
if not exist "C:\GIS" (
    echo Aanmaken map C:\GIS...
    mkdir "C:\GIS"
    if errorlevel 1 (
        echo FOUT: Kan C:\GIS niet aanmaken. Draai als administrator?
        pause
        exit /b 1
    )
)

echo.
echo Kopieer bezig van %SOURCE% naar C:\GIS...
echo Dit kan even duren, maar niet al te lang...
echo.

xcopy "%SOURCE%\*.*" "C:\GIS\" /E /I /Y /R /H /C /Q

if errorlevel 1 (
    echo.
    echo ER IS IETS MISGEGAAN tijdens het kopiëren.
    echo Controleer rechten, vrije ruimte of bronmap.
    echo.
    pause
    exit /b 1
)

echo.
echo ==============================================
echo Kopiëren succesvol afgerond!
echo Alles staat nu in C:\GIS
echo ==============================================
echo.

pause