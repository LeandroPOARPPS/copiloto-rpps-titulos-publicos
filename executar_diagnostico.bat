@echo off
cd /d "%~dp0"
echo Instalando/verificando dependencias...
py -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Nao foi possivel usar o comando "py". Tentando "python"...
    python -m pip install -r requirements.txt
)
echo.
echo Executando diagnostico...
py diagnostico_mercado.py
if errorlevel 9009 python diagnostico_mercado.py
pause
