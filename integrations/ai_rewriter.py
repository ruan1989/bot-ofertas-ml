# -*- coding: utf-8 -*-
"""
Reescrita de títulos/descrições usando Claude (claude-haiku-4-5).
Se ANTHROPIC_API_KEY não estiver definida, retorna None e o bot usa o título original.
"""
from __future__ import annotations

import os

_client = None


def _get_client():
    global _client
    if _client is None:
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def reescrever_titulo(produto: dict) -> str | None:
    """Retorna título reescrito ou None se IA indisponível."""
    client = _get_client()
    if client is None:
        return None

    titulo = produto.get("titulo", "")
    preco = produto.get("preco")
    preco_original = produto.get("preco_original")
    info_preco = ""
    if preco and preco_original and preco_original > preco:
        pct = int((1 - preco / preco_original) * 100)
        info_preco = f" ({pct}% OFF, de R${preco_original:.2f} por R${preco:.2f})"

    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            messages=[{
                "role": "user",
                "content": (
                    "Você é um copywriter para grupos de ofertas no Telegram brasileiro. "
                    "Reescreva o título abaixo de forma atraente, com senso de urgência, "
                    "em no máximo 2 linhas. Sem hashtags. Responda só com o texto reescrito.\n\n"
                    f"Produto: {titulo}{info_preco}"
                ),
            }],
        )
        return resp.content[0].text.strip()
    except Exception:
        return None
