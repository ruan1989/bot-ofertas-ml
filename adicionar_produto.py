# -*- coding: utf-8 -*-
"""
ADICIONAR PRODUTO À FILA
=========================
Assistente simples por linha de comando. Roda, faz 7 perguntas, salva tudo
certinho em produtos.json e calcula o score da oferta na hora.

Como usar:
    python adicionar_produto.py

Antes de rodar, gere o link de afiliado no app ou site do Mercado Livre:
  1. Abra o produto que você quer divulgar.
  2. Toque em "Compartilhar" (se a Barra de Afiliados estiver ativada) OU vá
     em Portal do Afiliado → Gerador de link → cole a URL → Gerar link.
  3. Cole o link gerado aqui quando solicitado.
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from core.scorer import calcular_score, COMISSOES_ML
from core.deduplicator import e_duplicata

ARQUIVO = "produtos.json"


def _carregar() -> list[dict]:
    if not os.path.exists(ARQUIVO):
        return []
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return json.loads(f.read().strip() or "[]")


def _salvar(produtos: list[dict]) -> None:
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)


def _pedir_preco(rotulo: str) -> float | None:
    valor = input(rotulo).strip().replace("R$", "").replace(",", ".").strip()
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        print("  (não entendi esse número, deixando em branco)")
        return None


def main() -> None:
    produtos = _carregar()

    print("=== Adicionar novo produto à fila ===\n")

    link = input("1) LINK DE AFILIADO (gerado no Portal do Afiliado ML): ").strip()
    if not link:
        print("Link em branco, cancelando.")
        return

    titulo = input("2) Título do produto (como vai aparecer na mensagem): ").strip()
    preco = _pedir_preco("3) Preço atual (ex: 149.90, ENTER se não souber): ")
    preco_original = _pedir_preco("4) Preço ANTES do desconto (ENTER se não houver): ")
    foto = input("5) Link da foto do produto (ENTER para sem foto): ").strip()

    cats = ", ".join(COMISSOES_ML.keys())
    categoria = input(f"6) Categoria ({cats}) [ENTER = geral]: ").strip().lower() or "geral"

    canal = input("7) Nome do canal (deve existir em CANAIS no bot_ofertas.py, ENTER = 'geral'): ").strip()

    novo = {
        "id": f"p{len(produtos) + 1}_{int(datetime.now().timestamp())}",
        "titulo": titulo or "Produto sem título",
        "preco": preco,
        "preco_original": preco_original,
        "link": link,
        "foto": foto or None,
        "categoria": categoria,
        "canal": canal or "geral",
        "status": "pendente",
        "adicionado_em": datetime.now().isoformat(),
    }

    novo["score"] = calcular_score(novo)

    if e_duplicata(novo):
        print(f"\n⚠️  Atenção: este produto parece duplicado (mesmo link ou título muito similar a um já enviado).")
        confirmar = input("Deseja adicionar mesmo assim? (s/N): ").strip().lower()
        if confirmar != "s":
            print("Cancelado.")
            return

    produtos.append(novo)
    _salvar(produtos)

    pendentes = sum(1 for p in produtos if p.get("status") not in ("enviado", "duplicata"))
    score = novo["score"]
    qualidade = "🟢 ótima" if score >= 75 else ("🟡 boa" if score >= 50 else "🔴 baixa")

    print(f"\n✅ Produto adicionado!")
    print(f"   Score da oferta: {score}/100 ({qualidade})")
    print(f"   {pendentes} produto(s) aguardando envio na fila.")
    print("   Rode 'python bot_ofertas.py' quando quiser disparar a fila.")


if __name__ == "__main__":
    main()
