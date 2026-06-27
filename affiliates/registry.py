# -*- coding: utf-8 -*-
"""
Registro central de provedores de afiliado.
Uso:
    from affiliates.registry import get_provider
    provider = get_provider("https://www.mercadolivre.com.br/...")
"""
from __future__ import annotations

from affiliates.base import AffiliateProvider
from affiliates.mercadolivre import MLAffiliateProvider
from affiliates.amazon import AmazonAffiliateProvider
from affiliates.shopee import ShopeeAffiliateProvider
from affiliates.magalu import MagaluAffiliateProvider
from affiliates.kabum import KabumAffiliateProvider

_PROVIDERS: list[AffiliateProvider] = [
    MLAffiliateProvider(),
    AmazonAffiliateProvider(),
    ShopeeAffiliateProvider(),
    MagaluAffiliateProvider(),
    KabumAffiliateProvider(),
]


def get_provider(url: str) -> AffiliateProvider | None:
    """Retorna o provedor correto para a URL, ou None se nenhum suporta."""
    for p in _PROVIDERS:
        if p.can_handle(url):
            return p
    return None


def health_report() -> dict[str, bool]:
    """Retorna status de saúde de todos os provedores."""
    return {p.name: p.health_check() for p in _PROVIDERS}
