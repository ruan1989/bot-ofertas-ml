# -*- coding: utf-8 -*-
"""
BOT DE OFERTAS - Orquestrador principal
========================================
Fluxo por execução:
  1. Carrega produtos pendentes
  2. Calcula score de cada um (desconto, comissão, qualidade)
  3. Ordena pelas melhores ofertas primeiro
  4. Filtra duplicatas (janela 30 dias)
  5. Reescreve título com IA (se ANTHROPIC_API_KEY estiver definida)
  6. Publica no canal Telegram configurado
  7. Registra no histórico para deduplicação futura

Como usar:
    python bot_ofertas.py
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
from telegram import Bot

from core.scorer import calcular_score
from core.deduplicator import e_duplicata, registrar_envio
from core.scheduler import resumo_horario, e_bom_momento
from integrations.ai_rewriter import reescrever_titulo
from integrations.telegram_bot import publicar

load_dotenv()

TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
if not TOKEN_TELEGRAM:
    raise RuntimeError("TOKEN_TELEGRAM não definido. Configure o arquivo .env")

CANAIS = {
    "geral": os.getenv("CANAL_GERAL", ""),
}

ARQUIVO_PRODUTOS = "produtos.json"
ARQUIVO_LOG = "envios.log"
INTERVALO_ENTRE_ENVIOS = 8

logging.basicConfig(
    filename=ARQUIVO_LOG,
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    encoding="utf-8",
)


def log(msg: str) -> None:
    print(msg)
    logging.info(msg)


def carregar_produtos() -> list[dict]:
    if not os.path.exists(ARQUIVO_PRODUTOS):
        return []
    with open(ARQUIVO_PRODUTOS, "r", encoding="utf-8") as f:
        return json.loads(f.read().strip() or "[]")


def salvar_produtos(produtos: list[dict]) -> None:
    with open(ARQUIVO_PRODUTOS, "w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)


async def main() -> None:
    log(f"\n{'='*50}")
    log(f"Bot Ofertas iniciado — {resumo_horario()}")

    if not e_bom_momento():
        log("⏰ Horário não ideal para publicação (score baixo). Prosseguindo mesmo assim...")

    produtos = carregar_produtos()
    if not produtos:
        log("Fila vazia. Use 'python adicionar_produto.py' para adicionar produtos.")
        return

    pendentes = [p for p in produtos if p.get("status") not in ("enviado", "duplicata")]
    if not pendentes:
        log("Nenhum produto novo pendente. Tudo já foi enviado.")
        return

    for p in pendentes:
        if not p.get("score"):
            p["score"] = calcular_score(p)

    pendentes.sort(key=lambda p: p.get("score", 0), reverse=True)
    log(f"Encontrados {len(pendentes)} produto(s) pendente(s). Iniciando envio...")

    tem_ia = bool(os.getenv("ANTHROPIC_API_KEY"))
    if tem_ia:
        log("🤖 Reescrita com IA ativada.")

    async with Bot(token=TOKEN_TELEGRAM) as bot:
        for produto in pendentes:
            log(f"\nProcessando: {produto['titulo']} (score {produto.get('score', 0)})")

            if e_duplicata(produto):
                produto["status"] = "duplicata"
                log("  ⏭️  Duplicata detectada — ignorada.")
                salvar_produtos(produtos)
                continue

            titulo_reescrito = reescrever_titulo(produto) if tem_ia else None
            if titulo_reescrito:
                log(f"  ✏️  Título reescrito: {titulo_reescrito}")

            sucesso = await publicar(bot, produto, CANAIS, titulo_reescrito)
            if sucesso:
                produto["status"] = "enviado"
                produto["enviado_em"] = datetime.now().isoformat()
                registrar_envio(produto)
                log("  ✅ Enviado com sucesso!")
            else:
                log("  ❌ Falha no envio. Será tentado novamente na próxima execução.")

            salvar_produtos(produtos)
            await asyncio.sleep(INTERVALO_ENTRE_ENVIOS)

    log("\nFinalizado.")


if __name__ == "__main__":
    asyncio.run(main())
