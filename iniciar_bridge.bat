@echo off
chcp 65001 > nul
title Bridge WhatsApp - Bot Ofertas
color 0A

echo.
echo  ================================================
echo   BRIDGE TELEGRAM ^> WHATSAPP  -  Bot Ofertas
echo  ================================================
echo.
echo  IMPORTANTE: Mantenha o WhatsApp Web aberto no
echo  Chrome antes de continuar!
echo.
echo  Pressione qualquer tecla para iniciar...
pause > nul

cd /d "%~dp0"
python bridge_whatsapp.py

echo.
echo Bridge encerrado. Pressione qualquer tecla para sair.
pause > nul
