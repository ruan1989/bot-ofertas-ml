# -*- coding: utf-8 -*-
"""
Pontuação de ofertas (0-100).
Pesos: desconto% (40), economia R$ (20), comissão ML (20), foto (10), título (10).
"""
from __future__ import annotations

COMISSOES_ML: dict[str, float] = {
    "beleza": 0.16,
    "moda": 0.14,
    "casa": 0.12,
    "moveis": 0.12,
    "brinquedos": 0.12,
    "esportes": 0.10,
    "eletronicos": 0.08,
    "informatica": 0.08,
    "games": 0.08,
    "automotivo": 0.06,
    "geral": 0.08,
}


def calcular_score(produto: dict) -> int:
    score = 0
    preco: float | None = produto.get("preco")
    preco_original: float | None = produto.get("preco_original")

    if preco and preco_original and preco_original > preco:
        pct_desconto = (1 - preco / preco_original) * 100
        score += min(40, int(pct_desconto))

        economia = preco_original - preco
        score += min(20, int(economia / 25))

    categoria = (produto.get("categoria") or "geral").lower()
    comissao = COMISSOES_ML.get(categoria, 0.08)
    score += int(comissao * 125)  # 16%→20 pts, 8%→10 pts

    if produto.get("foto"):
        score += 10

    titulo = produto.get("titulo", "")
    if len(titulo) >= 20:
        score += 5
    if len(titulo) >= 50:
        score += 5

    return min(100, score)
