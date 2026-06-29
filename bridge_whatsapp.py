# -*- coding: utf-8 -*-
"""
BRIDGE TELEGRAM → WHATSAPP
===========================
Monitora o canal Telegram em tempo real e envia cada nova oferta
automaticamente para o grupo WhatsApp, usando IA para gerar o conteúdo.

Pré-requisitos:
  - WhatsApp Web aberto no Chrome (aba ativa com sessão logada)
  - .env configurado com TOKEN_TELEGRAM, CANAL_GERAL, WHATSAPP_GROUP_ID

Como usar:
  python bridge_whatsapp.py

Dica: execute via iniciar_bridge.bat para iniciar automaticamente.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import asyncio
import logging
import os
import re
import time

from dotenv import load_dotenv
load_dotenv()

from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [BRIDGE] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/bridge.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN_TELEGRAM", "")
CANAL_ID = os.getenv("CANAL_GERAL", "")
GROUP_ID = os.getenv("WHATSAPP_GROUP_ID", "")

# IDs de mensagem já processadas (evita duplicatas na mesma sessão)
_processados: set[int] = set()


def _extrair_produto_da_mensagem(texto: str, entidade_urls: list = None) -> dict | None:
    """Extrai dados básicos do produto a partir do texto do Telegram."""
    if not texto:
        return None

    # Extrai link
    link = ""
    if entidade_urls:
        for url in entidade_urls:
            if url:
                link = url
                break
    if not link:
        m = re.search(r"https?://\S+", texto)
        link = m.group(0) if m else ""

    # Extrai título (primeira linha não-vazia após emoji)
    linhas = [l.strip() for l in texto.split("\n") if l.strip()]
    titulo = ""
    for linha in linhas:
        # Remove emojis e marcadores do início
        limpa = re.sub(r"^[🔥💰🏷️✅➡️#\s*<>b/]+", "", linha).strip()
        if len(limpa) > 10:
            titulo = limpa[:80]
            break

    # Extrai preço
    preco = None
    m_preco = re.search(r"R\$\s*([\d.,]+)", texto)
    if m_preco:
        try:
            preco = float(m_preco.group(1).replace(".", "").replace(",", "."))
        except Exception:
            pass

    # Extrai desconto
    desconto_pct = 0
    m_desc = re.search(r"(\d+)%\s*OFF", texto, re.IGNORECASE)
    if m_desc:
        desconto_pct = int(m_desc.group(1))

    # Extrai cupom
    cupom = None
    m_cupom = re.search(r"CUPOM[:\s]+([A-Z0-9\-_]+)", texto, re.IGNORECASE)
    if m_cupom:
        cupom = m_cupom.group(1)

    if not titulo and not link:
        return None

    return {
        "titulo": titulo or "Oferta especial",
        "link": link,
        "preco": preco,
        "desconto_pct": desconto_pct,
        "cupom": cupom,
        "categoria": "geral",
    }


async def _enviar_whatsapp(produto: dict, texto_original: str) -> bool:
    """Gera conteúdo IA e envia para WhatsApp."""
    try:
        from core.ai_content import gerar_conteudo
        conteudo = gerar_conteudo(produto)
        mensagem_wa = conteudo.get("mensagem_whatsapp") or texto_original[:500]
        ia_usada = conteudo.get("ia_usada", False)
        log.info("Conteúdo %s para: %s", "IA ✨" if ia_usada else "padrão", produto.get("titulo", "")[:50])
    except Exception as e:
        log.warning("IA falhou: %s — usando texto original", e)
        mensagem_wa = texto_original[:500]

    if not GROUP_ID:
        log.warning("WHATSAPP_GROUP_ID não configurado")
        return False

    if os.getenv("GITHUB_ACTIONS"):
        log.info("GitHub Actions detectado — pywhatkit ignorado")
        return False

    try:
        import pywhatkit
        pywhatkit.sendwhatmsg_to_group_instantly(
            group_id=GROUP_ID,
            message=mensagem_wa,
            wait_time=12,
            tab_close=True,
            close_time=3,
        )
        log.info("✅ WhatsApp enviado para grupo %s", GROUP_ID)
        return True
    except ImportError:
        log.error("pywhatkit não instalado. Execute: pip install pywhatkit")
        return False
    except Exception as e:
        log.error("pywhatkit falhou: %s", e)
        return False


async def _handler_nova_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa nova mensagem do canal Telegram."""
    msg = update.channel_post or update.message
    if not msg:
        return

    # Só processa mensagens do canal configurado
    chat_id = str(msg.chat_id)
    if CANAL_ID and chat_id != str(CANAL_ID):
        return

    msg_id = msg.message_id
    if msg_id in _processados:
        return
    _processados.add(msg_id)

    texto = msg.text or msg.caption or ""
    if not texto or len(texto) < 20:
        return

    # Filtra apenas mensagens de oferta (contêm link de produto)
    if not re.search(r"(meli\.la|mercadolivre\.com|amazon\.com\.br|amzn\.to)", texto, re.I):
        return

    log.info("Nova oferta detectada (msg #%d) — enviando para WhatsApp...", msg_id)

    # Extrai URLs das entidades
    urls = []
    if msg.entities:
        for ent in msg.entities:
            if ent.url:
                urls.append(ent.url)
    if msg.caption_entities:
        for ent in msg.caption_entities:
            if ent.url:
                urls.append(ent.url)

    produto = _extrair_produto_da_mensagem(texto, urls)
    if not produto:
        log.warning("Não consegui extrair produto da mensagem #%d", msg_id)
        return

    # Pequena pausa para não travar o WhatsApp Web
    await asyncio.sleep(3)
    await _enviar_whatsapp(produto, texto)


def main():
    if not TOKEN:
        print("❌ TOKEN_TELEGRAM não configurado no .env")
        return
    if not GROUP_ID:
        print("⚠️  WHATSAPP_GROUP_ID não configurado — WhatsApp desativado")

    print("=" * 55)
    print("🌉 BRIDGE TELEGRAM → WHATSAPP")
    print("=" * 55)
    print(f"📡 Monitorando canal: {CANAL_ID or 'todos'}")
    print(f"💚 Grupo WhatsApp: {GROUP_ID or 'não configurado'}")
    print(f"🤖 IA: {'ativa (Claude Sonnet)' if _ia_ok() else 'inativa (sem API key)'}")
    print("Ctrl+C para parar.\n")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(
        filters.ALL & (filters.ChatType.CHANNEL | filters.ChatType.GROUPS),
        _handler_nova_mensagem,
    ))
    app.run_polling(allowed_updates=["channel_post", "message"])


def _ia_ok() -> bool:
    try:
        from core.ai_content import ia_ativa
        return ia_ativa()
    except Exception:
        return False


if __name__ == "__main__":
    main()
