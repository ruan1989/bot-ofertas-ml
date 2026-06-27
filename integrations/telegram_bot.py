# -*- coding: utf-8 -*-
"""
Publicação de ofertas e chatbot de FAQ no Telegram.
"""
from __future__ import annotations

import html
import logging
from telegram import Bot
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)
from telegram import Update

_FAQ: dict[str, str] = {
    "frete": "A maioria dos produtos tem frete grátis para assinantes Prime. Confira na página do produto.",
    "garantia": "Todos os produtos têm garantia do vendedor e proteção Mercado Livre.",
    "prazo": "O prazo de entrega aparece antes de finalizar a compra, na página do produto.",
    "autenticidade": "Publicamos apenas ofertas de vendedores com reputação verde no Mercado Livre.",
    "desconto": "Os descontos são calculados com base no preço original registrado no momento da publicação.",
    "devolucao": "O Mercado Livre oferece política de devolução em até 7 dias após o recebimento.",
}


def _montar_mensagem(produto: dict, titulo_reescrito: str | None = None) -> str:
    titulo = html.escape(titulo_reescrito or produto["titulo"])
    preco: float | None = produto.get("preco")
    preco_original: float | None = produto.get("preco_original")
    link = produto["link"]
    score: int = produto.get("score", 0)

    linhas = [f"🛍️ <b>{titulo}</b>", ""]

    if preco_original and preco and preco_original > preco:
        desconto = int(round((1 - preco / preco_original) * 100))
        linhas.append(
            f"De <s>R$ {preco_original:.2f}</s> por <b>R$ {preco:.2f}</b> "
            f"({desconto}% OFF) 🔥"
        )
    elif preco:
        linhas.append(f"💰 R$ {preco:.2f}")

    if score >= 75:
        linhas.append("⭐ <i>Oferta em destaque</i>")

    linhas += [
        "",
        f'🔗 <a href="{html.escape(link, quote=True)}">Ver oferta no Mercado Livre</a>',
        "",
        "#publicidade",
    ]
    return "\n".join(linhas)


async def publicar(bot: Bot, produto: dict, canais: dict, titulo_reescrito: str | None = None) -> bool:
    canal_nome = produto.get("canal") or "geral"
    chat_id = canais.get(canal_nome) or next(iter(canais.values()))
    mensagem = _montar_mensagem(produto, titulo_reescrito)
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
        logging.error(f"Erro ao publicar '{produto.get('titulo')}': {e}")
        return False


async def _cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Olá! Sou o assistente de ofertas. Pode me perguntar sobre "
        "frete, garantia, prazo, devolução ou autenticidade dos produtos."
    )


async def _cmd_ofertas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Acompanhe o canal para as melhores ofertas do dia! 🛍️")


async def _responder_faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    texto = (update.message.text or "").lower()
    for palavra, resposta in _FAQ.items():
        if palavra in texto:
            await update.message.reply_text(resposta)
            return
    await update.message.reply_text(
        "Não entendi sua dúvida. Pode me perguntar sobre: "
        + ", ".join(_FAQ.keys()) + "."
    )


def criar_aplicacao(token: str):
    """Cria o Application do telegram para rodar o chatbot em modo polling."""
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", _cmd_start))
    app.add_handler(CommandHandler("ofertas", _cmd_ofertas))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _responder_faq))
    return app
