# -*- coding: utf-8 -*-
"""Stub — Shopee Affiliate (futuro)."""
from __future__ import annotations
from affiliates.base import AffiliateProvider


class ShopeeAffiliateProvider(AffiliateProvider):
    name = "shopee"

    def can_handle(self, url: str) -> bool:
        return "shopee.com.br" in url

    def validate_affiliate_link(self, link: str) -> bool:
        return link is not None and "shopee.com.br" in link and "af_id=" in link

    def health_check(self) -> bool:
        return False

    def generate_affiliate_link(self, url: str) -> str | None:
        return None
