@echo off
title HUB3 JARVIS v4.1
color 0B

echo ========================================
echo   HUB3 JARVIS v4.1 - Iniciando (Windows)
echo ========================================
echo.

REM Detectar letra do HD externo
set "HD_ROOT="
for %%D in (D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if exist "%%D:\JARVIS HUB3\hub3-jarvis\backend" (
        set "HD_ROOT=%%D:\JARVIS HUB3"
        goto FOUND
    )
)
echo ERRO: HD JARVIS HUB3 nao encontrado!
echo Conecte o HD externo e tente novamente.
pause
exit /b 1

:FOUND
echo >> HD encontrado: %HD_ROOT%
echo.

REM Verificar MongoDB
echo >> Verificando MongoDB...
tasklist | findstr mongod >nul
if %errorlevel% equ 0 (
    echo >> MongoDB ja esta rodando.
) else (
    echo >> Iniciando MongoDB...
    start /b mongod --dbpath "%HD_ROOT%\mongodb-data" --logpath "%HD_ROOT%\mongodb-logs\mongod.log"
    timeout /t 5 /nobreak >nul
)

REM Verificar Python
echo >> Verificando Python...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado no Windows!
    echo Instale Python 3.9+ de python.org
    pause
    exit /b 1
)

REM Criar venv no Windows se nao existir
if not exist "%HD_ROOT%\hub3-jarvis\backend\venv-win" (
    echo >> Criando ambiente virtual para Windows...
    cd /d "%HD_ROOT%\hub3-jarvis\backend"
    python -m venv venv-win
    call venv-win\Scripts\activate
    pip install -r requirements.txt
    pip install "motor==3.3.2" "pymongo==4.6.3"
) else (
    call "%HD_ROOT%\hub3-jarvis\backend\venv-win\Scripts\activate"
)

REM Subir backend
echo >> Subindo backend FastAPI...
cd /d "%HD_ROOT%\hub3-jarvis\backend"
start /b uvicorn main:app --host 0.0.0.0 --port 8000
timeout /t 5 /nobreak >nul

REM Abrir navegador
echo >> Abrindo interface no navegador...
start http://localhost:8000

if exist "%HD_ROOT%\hub3-jarvis\frontend\index.html" (
    start "" "%HD_ROOT%\hub3-jarvis\frontend\index.html"
)

echo.
echo ========================================
echo   HUB3 JARVIS v4.1 - ONLINE!
echo   Backend: http://localhost:8000
echo   Para parar: feche esta janela
echo ========================================
echo.
pause

REM Parar MongoDB ao fechar
taskkill /f /im mongod.exe >nul 2>nul
