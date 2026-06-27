# -*- coding: utf-8 -*-
"""
BOT DE OFERTAS - Envio automático para Telegram
=================================================
Este script NÃO busca produtos no Mercado Livre (esse caminho está bloqueado
pela própria plataforma para apps não-certificados). Em vez disso, ele lê uma
fila de produtos que VOCÊ adicionou (com adicionar_produto.py) usando o link
de afiliado oficial, e cuida de tudo o resto automaticamente:

  - Formata a mensagem (preço, desconto, foto, link)
  - Envia para o(s) canal(is) certo(s) do Telegram
  - Marca o que já foi enviado (nunca manda o mesmo produto duas vezes)
  - Registra tudo em um arquivo de log

Como usar:
    python bot_ofertas.py

Rode esse comando sempre que quiser "disparar" os produtos pendentes da fila.
Para automatizar isso (rodar sozinho de hora em hora), veja o LEIA-ME.md.
"""

import json
import os
import html
import asyncio
import logging
from datetime import datetime

from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import ParseMode

load_dotenv()

# ===================== CONFIGURAÇÃO =====================
# Token do seu bot (obtido com o @BotFather no Telegram).
# Defina essas variáveis no arquivo .env — nunca coloque valores reais aqui no código.
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
if not TOKEN_TELEGRAM:
    raise RuntimeError("Variável de ambiente TOKEN_TELEGRAM não definida. Configure o arquivo .env")

# Canais do Telegram onde o bot vai postar. A chave (ex: "geral") é o nome
# que você usa no campo "canal" quando adiciona um produto com
# adicionar_produto.py. Adicione mais linhas para criar canais por nicho.
CANAIS = {
    "geral": os.getenv("CANAL_GERAL", ""),
    # "eletronicos": os.getenv("CANAL_ELETRONICOS", ""),
    # "beleza":      os.getenv("CANAL_BELEZA", ""),
}

ARQUIVO_PRODUTOS = "produtos.json"
ARQUIVO_LOG = "envios.log"
INTERVALO_ENTRE_ENVIOS = 8  # segundos de pausa entre cada post (evita limite do Telegram)
# ==========================================================

logging.basicConfig(
    filename=ARQUIVO_LOG,
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    encoding="utf-8",
)


def log(msg: str):
    print(msg)
    logging.info(msg)


def carregar_produtos():
    if not os.path.exists(ARQUIVO_PRODUTOS):
        return []
    with open(ARQUIVO_PRODUTOS, "r", encoding="utf-8") as f:
        conteudo = f.read().strip()
        return json.loads(conteudo) if conteudo else []


def salvar_produtos(produtos):
    with open(ARQUIVO_PRODUTOS, "w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)


def montar_mensagem(produto):
    titulo = html.escape(produto["titulo"])
    preco = produto.get("preco")
    preco_original = produto.get("preco_original")
    link = produto["link"]

    linhas = [f"🛍️ <b>{titulo}</b>", ""]

    if preco_original and preco and preco_original > preco:
        desconto = int(round((1 - preco / preco_original) * 100))
        linhas.append(
            f"De <s>R$ {preco_original:.2f}</s> por <b>R$ {preco:.2f}</b> "
            f"({desconto}% OFF) 🔥"
        )
    elif preco:
        linhas.append(f"💰 R$ {preco:.2f}")

    linhas.append("")
    linhas.append(f'🔗 <a href="{html.escape(link, quote=True)}">Ver oferta no Mercado Livre</a>')
    linhas.append("")
    linhas.append("#publicidade")
    return "\n".join(linhas)


async def enviar_produto(bot, produto):
    canal_nome = produto.get("canal") or "geral"
    chat_id = CANAIS.get(canal_nome) or next(iter(CANAIS.values()))
    mensagem = montar_mensagem(produto)
    try:
        if produto.get("foto"):
            await bot.send_photo(
                chat_id=chat_id,
                photo=produto["foto"],
                caption=mensagem,
                parse_mode=ParseMode.HTML,
            )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=mensagem,
                parse_mode=ParseMode.HTML,
            )
        return True
    except Exception as e:
        log(f"  ❌ Erro ao enviar '{produto.get('titulo')}': {e}")
        return False


async def main():
    produtos = carregar_produtos()
    pendentes = [p for p in produtos if p.get("status") != "enviado"]

    if not produtos:
        log("Fila vazia. Use 'python adicionar_produto.py' para adicionar produtos primeiro.")
        return

    if not pendentes:
        log("Nenhum produto novo pendente. Tudo que está na fila já foi enviado.")
        return

    log(f"Encontrados {len(pendentes)} produto(s) pendente(s). Iniciando envio...")

    async with Bot(token=TOKEN_TELEGRAM) as bot:
        for produto in pendentes:
            log(f"Enviando: {produto['titulo']}")
            sucesso = await enviar_produto(bot, produto)
            if sucesso:
                produto["status"] = "enviado"
                produto["enviado_em"] = datetime.now().isoformat()
                log("  ✅ Enviado com sucesso!")
            salvar_produtos(produtos)
            await asyncio.sleep(INTERVALO_ENTRE_ENVIOS)

    log("Finalizado.")


if __name__ == "__main__":
    asyncio.run(main())
