# -*- coding: utf-8 -*-
"""
Interface abstrata para provedores de links de afiliado.
Cada plataforma (ML, Amazon, Shopee, etc.) implementa esta interface.
"""
from __future__ import annotations
from abc import ABC, abstractmethod


class AffiliateProvider(ABC):
    """Contrato que todo provedor de afiliado deve implementar."""

    name: str  # identificador único, ex: "mercadolivre"

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Retorna True se este provedor consegue gerar link para a URL."""
        ...

    @abstractmethod
    def generate_affiliate_link(self, url: str) -> str | None:
        """
        Gera um link oficial de afiliado para a URL do produto.
        Retorna o link rastreável ou None em caso de falha.
        NÃO adiciona parâmetros manualmente — usa apenas o mecanismo
        oficial da plataforma.
        """
        ...

    @abstractmethod
    def validate_affiliate_link(self, link: str) -> bool:
        """Verifica se o link é um link de afiliado oficial válido."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Verifica se o provedor está autenticado e disponível."""
        ...

    async def generate_affiliate_link_async(self, url: str) -> str | None:
        """
        Versão async de generate_affiliate_link.
        Implementação padrão: roda a versão síncrona num executor de thread.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate_affiliate_link, url)
