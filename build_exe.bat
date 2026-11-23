@echo off
chcp 65001 >nul
echo ======================================================================
echo    COMPILAÇÃO DO OBSIDIAN BOOST PRIME — EDIÇÃO COM DISCORD LIVRE
echo ======================================================================
echo.

cd /d "%~dp0"

echo [1/2] Verificando dependencias Python...
python -m pip install -r requirements.txt

echo.
echo [2/2] Compilando executavel standalone com PyInstaller (--uac-admin)...
python -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --uac-admin ^
    --icon="app.ico" ^
    --add-data="app.ico;." ^
    --collect-all customtkinter ^
    --collect-all pystray ^
    --name="ObsidianBoost_Prime" ^
    main.py

echo.
if %ERRORLEVEL% EQU 0 (
    echo ======================================================================
    echo [SUCESSO] Build concluida com exito!
    echo Arquivo final: dist\ObsidianBoost_Prime.exe
    echo ======================================================================
) else (
    echo ======================================================================
    echo [ERRO] Ocorreu uma falha durante a compilacao com o PyInstaller.
    echo ======================================================================
)
