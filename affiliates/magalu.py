# -*- coding: utf-8 -*-
"""Stub — Magazine Luiza Affiliate (futuro)."""
from __future__ import annotations
from affiliates.base import AffiliateProvider


class MagaluAffiliateProvider(AffiliateProvider):
    name = "magalu"

    def can_handle(self, url: str) -> bool:
        return "magazinevoce.com.br" in url or "magazineluiza.com.br" in url

    def validate_affiliate_link(self, link: str) -> bool:
        return link is not None and "magazinevoce.com.br" in link

    def health_check(self) -> bool:
        return False

    def generate_affiliate_link(self, url: str) -> str | None:
        return None
