# -*- coding: utf-8 -*-
"""
Provedor de links de afiliado da Amazon Brasil.
Stub — implementação futura via Amazon Associates / tag de afiliado.
"""
from __future__ import annotations
from affiliates.base import AffiliateProvider


class AmazonAffiliateProvider(AffiliateProvider):
    name = "amazon"

    def can_handle(self, url: str) -> bool:
        return "amazon.com.br" in url or "amzn.to" in url

    def validate_affiliate_link(self, link: str) -> bool:
        return link is not None and ("amzn.to" in link or "tag=" in link)

    def health_check(self) -> bool:
        return False  # não implementado

    def generate_affiliate_link(self, url: str) -> str | None:
        # TODO: usar Amazon Associates API com tag de afiliado
        # Por enquanto, não publicar sem link oficial
        return None
