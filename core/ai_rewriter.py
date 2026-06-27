# -*- coding: utf-8 -*-
"""
Reescrita de títulos e descrições de produtos usando Claude Haiku via SDK Anthropic.

- Usa ANTHROPIC_API_KEY do .env (fallback gracioso se ausente).
- Cache em memória para evitar reescritas duplicadas na mesma execução.
- Timeout de 5 segundos; todas as exceções retornam None sem propagar erros.
"""
from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ── Configuração ──────────────────────────────────────────────────────────────

_MODELO = "claude-haiku-4-5-20251001"
_MAX_TOKENS_TITULO = 80
_MAX_TOKENS_DESCRICAO = 200
_TIMEOUT_SEGUNDOS = 5.0

# Cache em memória: {produto_id: {"titulo": str, "descricao": str}}
_cache: dict[str, dict[str, Optional[str]]] = {}

# ── Inicialização do cliente Anthropic ───────────────────────────────────────

_client = None


def _get_client():
    """Retorna o cliente Anthropic, criando-o na primeira chamada.
    Retorna None se ANTHROPIC_API_KEY não estiver configurada."""
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        import anthropic  # noqa: PLC0415

        _client = anthropic.Anthropic(
            api_key=api_key,
            timeout=_TIMEOUT_SEGUNDOS,
        )
        return _client
    except Exception:
        return None


# ── Funções auxiliares ────────────────────────────────────────────────────────

def _produto_id(produto: dict) -> str:
    """Chave de cache baseada no ID ou título do produto."""
    return str(produto.get("id") or produto.get("produto_id") or produto.get("titulo", ""))


def _formatar_contexto(produto: dict) -> str:
    """Monta string de contexto do produto para o prompt."""
    titulo = produto.get("titulo", "")
    preco = produto.get("preco")
    preco_original = produto.get("preco_original")
    desconto_pct = produto.get("desconto_pct")
    categoria = produto.get("categoria", "geral")

    if preco_original and preco and not desconto_pct:
        desconto_pct = round((1 - preco / preco_original) * 100, 1)

    partes = [f"Título original: {titulo}"]
    if preco:
        partes.append(f"Preço atual: R$ {preco:.2f}")
    if preco_original:
        partes.append(f"Preço original: R$ {preco_original:.2f}")
    if desconto_pct:
        partes.append(f"Desconto: {desconto_pct:.0f}%")
    if categoria:
        partes.append(f"Categoria: {categoria}")

    return "\n".join(partes)


# ── Funções públicas ──────────────────────────────────────────────────────────

def reescrever_titulo(produto: dict) -> Optional[str]:
    """Reescreve o título do produto de forma atrativa para o Telegram.

    Args:
        produto: dict com keys titulo, preco, preco_original, desconto_pct, categoria.

    Returns:
        Título reescrito (máx. 60 caracteres) com emojis, tom urgente/econômico.
        Retorna None se a API não estiver disponível ou ocorrer qualquer erro.
    """
    pid = _produto_id(produto)

    # Verificar cache
    if pid and pid in _cache and "titulo" in _cache[pid]:
        return _cache[pid]["titulo"]

    client = _get_client()
    if client is None:
        return None

    try:
        contexto = _formatar_contexto(produto)
        prompt = (
            f"{contexto}\n\n"
            "Reescreva o título acima para um post de oferta no Telegram. "
            "Regras OBRIGATÓRIAS:\n"
            "- Máximo 60 caracteres (incluindo emojis)\n"
            "- Use 1-2 emojis relevantes\n"
            "- Tom urgente e econômico (ex: 'OFERTA', 'PREÇO BAIXO', 'TOP')\n"
            "- Destaque o desconto se for relevante\n"
            "- Responda APENAS com o título reescrito, sem aspas, sem explicações."
        )

        response = client.messages.create(
            model=_MODELO,
            max_tokens=_MAX_TOKENS_TITULO,
            messages=[{"role": "user", "content": prompt}],
        )

        titulo_novo = None
        for block in response.content:
            if block.type == "text":
                titulo_novo = block.text.strip().strip('"').strip("'")
                # Garantir limite de 60 caracteres
                if len(titulo_novo) > 60:
                    titulo_novo = titulo_novo[:60].rstrip()
                break

        # Salvar no cache
        if pid:
            if pid not in _cache:
                _cache[pid] = {}
            _cache[pid]["titulo"] = titulo_novo

        return titulo_novo

    except Exception:
        return None


def reescrever_descricao(produto: dict) -> Optional[str]:
    """Gera descrição curta do produto para o post no Telegram.

    Args:
        produto: dict com keys titulo, preco, preco_original, desconto_pct, categoria.

    Returns:
        Descrição de 2-3 linhas com principais benefícios, pronta para Telegram.
        Retorna None se a API não estiver disponível ou ocorrer qualquer erro.
    """
    pid = _produto_id(produto)

    # Verificar cache
    if pid and pid in _cache and "descricao" in _cache[pid]:
        return _cache[pid]["descricao"]

    client = _get_client()
    if client is None:
        return None

    try:
        contexto = _formatar_contexto(produto)
        prompt = (
            f"{contexto}\n\n"
            "Escreva uma descrição curta para um post de oferta no Telegram. "
            "Regras OBRIGATÓRIAS:\n"
            "- Exatamente 2-3 linhas\n"
            "- Destaque os principais benefícios do produto\n"
            "- Mencione o desconto e economia em reais se disponíveis\n"
            "- Use linguagem direta, empolgante e informal\n"
            "- Pode usar 1-2 emojis por linha\n"
            "- Responda APENAS com a descrição, sem título, sem explicações."
        )

        response = client.messages.create(
            model=_MODELO,
            max_tokens=_MAX_TOKENS_DESCRICAO,
            messages=[{"role": "user", "content": prompt}],
        )

        descricao = None
        for block in response.content:
            if block.type == "text":
                descricao = block.text.strip()
                break

        # Salvar no cache
        if pid:
            if pid not in _cache:
                _cache[pid] = {}
            _cache[pid]["descricao"] = descricao

        return descricao

    except Exception:
        return None


def limpar_cache() -> None:
    """Limpa o cache em memória (útil para testes)."""
    _cache.clear()
