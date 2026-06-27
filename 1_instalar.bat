@echo off
cd /d "%~dp0"
echo Instalando as bibliotecas necessarias (so precisa rodar isso 1 vez)...
echo.
pip install -r requirements.txt
echo.
echo ============================================
echo  Pronto! Pode fechar esta janela.
echo ============================================
pause
