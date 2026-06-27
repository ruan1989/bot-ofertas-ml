# -*- coding: utf-8 -*-
"""Stub — KaBuM! Affiliate (futuro)."""
from __future__ import annotations
from affiliates.base import AffiliateProvider


class KabumAffiliateProvider(AffiliateProvider):
    name = "kabum"

    def can_handle(self, url: str) -> bool:
        return "kabum.com.br" in url

    def validate_affiliate_link(self, link: str) -> bool:
        return link is not None and "kabum.com.br" in link

    def health_check(self) -> bool:
        return False

    def generate_affiliate_link(self, url: str) -> str | None:
        return None
