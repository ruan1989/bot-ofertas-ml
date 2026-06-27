# -*- coding: utf-8 -*-
"""
Gerador de links oficiais de afiliado do Mercado Livre.

Fluxo:
1. (Uma vez) `python -m integrations.ml_link_gen setup`
   → Abre o navegador, você faz login no ML, as cookies são salvas.
2. `gerar_link(url)` usa as cookies salvas para acessar o gerador de links
   do portal de afiliados e retorna um link meli.la oficial.
"""
from __future__ import annotations

import json
import os
import sys
import time

_DIR = os.path.dirname(os.path.abspath(__file__))
_COOKIES_FILE = os.path.join(_DIR, "..", "data", "ml_cookies.json")
_TOOL_ID = os.getenv("ML_AFFILIATE_TOOL_ID", "47114387")

_PORTAL_HUB = "https://www.mercadolivre.com.br/afiliados/hub"
_PORTAL_GERADOR = "https://www.mercadolivre.com.br/afiliados/tools/link-generator"
_LOGIN_URL = "https://www.mercadolivre.com.br"


def _cookies_existem() -> bool:
    return os.path.exists(_COOKIES_FILE)


def setup_sessao() -> None:
    """
    Abre um navegador VISÍVEL para você fazer login no Mercado Livre.
    As cookies de sessão são salvas em data/ml_cookies.json.
    Execute UMA VEZ:  python -m integrations.ml_link_gen setup
    """
    from playwright.sync_api import sync_playwright

    print("\n=== CONFIGURAÇÃO DO PORTAL DE AFILIADOS ===")
    print("Um navegador será aberto. Faça login com sua conta do ML.")
    print("Após entrar no portal de afiliados, feche o navegador ou pressione Enter aqui.\n")
    input("Pressione ENTER para abrir o navegador...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        ctx = browser.new_context(
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            no_viewport=True,
        )
        page = ctx.new_page()
        page.goto(_PORTAL_HUB, wait_until="domcontentloaded")

        print("\nAguardando você fazer login e chegar ao portal de afiliados...")
        print("(Pressione Ctrl+C aqui quando estiver logado no portal)")

        # Aguarda até estar logado no portal (URL muda para /hub sem redirect de login)
        while True:
            try:
                url_atual = page.url
                if "afiliados/hub" in url_atual or "afiliados/tools" in url_atual:
                    print(f"\n✅ Login detectado: {url_atual}")
                    time.sleep(2)
                    break
                time.sleep(1)
            except KeyboardInterrupt:
                break
            except Exception:
                time.sleep(1)

        # Salva cookies
        cookies = ctx.cookies()
        os.makedirs(os.path.dirname(_COOKIES_FILE), exist_ok=True)
        with open(_COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        print(f"✅ {len(cookies)} cookies salvas em: {_COOKIES_FILE}")
        browser.close()

    print("\nConfiguração concluída! O bot agora pode gerar links de afiliado automaticamente.")


def _carregar_cookies() -> list[dict]:
    if not _cookies_existem():
        raise FileNotFoundError(
            "Sessão do ML não configurada.\n"
            "Execute: python -m integrations.ml_link_gen setup"
        )
    with open(_COOKIES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def gerar_link(url_produto: str) -> str | None:
    """
    Gera um link oficial meli.la de afiliado para a URL do produto.
    Usa a sessão salva com setup_sessao().
    Retorna None se falhar.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

    try:
        cookies = _carregar_cookies()
    except FileNotFoundError as e:
        print(f"  ⚠️  {e}")
        return None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        # Captura requisições de API para pegar o link gerado
        link_meli = None
        api_respostas = []

        def on_response(resp):
            if "link" in resp.url.lower() or "short" in resp.url.lower():
                try:
                    body = resp.json()
                    api_respostas.append({"url": resp.url, "body": body})
                except Exception:
                    pass

        page.on("response", on_response)

        try:
            page.goto(_PORTAL_GERADOR, wait_until="networkidle", timeout=25000)
        except PlaywrightTimeout:
            page.goto(_PORTAL_GERADOR, wait_until="domcontentloaded", timeout=15000)

        # Verifica se está logado (não redirecionou para login)
        if "lgz/login" in page.url or "login" in page.url.lower():
            print("  ⚠️  Sessão expirada. Execute: python -m integrations.ml_link_gen setup")
            browser.close()
            return None

        # Aguarda o campo de URL aparecer
        try:
            page.wait_for_selector('input[type="url"], input[type="text"], input[placeholder*="URL"], input[placeholder*="url"], input[placeholder*="link"], input[placeholder*="Link"]', timeout=10000)
        except PlaywrightTimeout:
            # Tenta via JavaScript inspecionando o DOM
            pass

        page.screenshot(path=os.path.join(os.path.dirname(_COOKIES_FILE), "link_gen.png"))

        # Tenta encontrar o campo de input e preencher
        # Seletores possíveis do gerador de links
        seletores_input = [
            'input[placeholder*="URL"]',
            'input[placeholder*="url"]',
            'input[placeholder*="link"]',
            'input[placeholder*="Link"]',
            'input[name="url"]',
            'input[name="link"]',
            'input[type="url"]',
            '.andes-form-control__field',
            'input[class*="input"]',
        ]

        campo = None
        for sel in seletores_input:
            try:
                el = page.query_selector(sel)
                if el:
                    campo = el
                    break
            except Exception:
                pass

        if campo:
            campo.fill(url_produto)
            page.keyboard.press("Enter")

            # Aguarda resposta (link gerado)
            try:
                page.wait_for_selector(
                    'input[value*="meli.la"], a[href*="meli.la"], [class*="result"] input, [class*="generated"]',
                    timeout=10000
                )
            except PlaywrightTimeout:
                pass

            # Extrai link meli.la do DOM
            link_meli = page.evaluate("""
                () => {
                    // Procura em inputs
                    const inputs = Array.from(document.querySelectorAll('input'));
                    for (const inp of inputs) {
                        if (inp.value && inp.value.includes('meli.la')) return inp.value;
                    }
                    // Procura em links
                    const links = Array.from(document.querySelectorAll('a'));
                    for (const a of links) {
                        if (a.href && a.href.includes('meli.la')) return a.href;
                        if (a.textContent && a.textContent.includes('meli.la')) return a.textContent.trim();
                    }
                    // Procura no texto da página
                    const body = document.body.innerHTML;
                    const m = body.match(/https?:\\/\\/meli\\.la\\/[A-Za-z0-9]+/);
                    return m ? m[0] : null;
                }
            """)

        # Verifica resposta de API capturada
        if not link_meli:
            for resp in api_respostas:
                body = resp.get("body", {})
                if isinstance(body, dict):
                    link_meli = body.get("short_url") or body.get("link") or body.get("url")
                    if link_meli and "meli.la" in link_meli:
                        break

        browser.close()

    return link_meli


async def gerar_link_async(url_produto: str) -> str | None:
    """Versão async de gerar_link — para uso dentro de asyncio (rastreador.py)."""
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

    try:
        cookies = _carregar_cookies()
    except FileNotFoundError as e:
        print(f"  ⚠️  {e}")
        return None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )
        await ctx.add_cookies(cookies)
        page = await ctx.new_page()

        api_respostas = []

        def on_response(resp):
            if "link" in resp.url.lower() or "short" in resp.url.lower():
                async def _capture():
                    try:
                        body = await resp.json()
                        api_respostas.append({"url": resp.url, "body": body})
                    except Exception:
                        pass
                import asyncio
                asyncio.get_event_loop().create_task(_capture())

        page.on("response", on_response)

        try:
            await page.goto(_PORTAL_GERADOR, wait_until="networkidle", timeout=25000)
        except PlaywrightTimeout:
            await page.goto(_PORTAL_GERADOR, wait_until="domcontentloaded", timeout=15000)

        if "lgz/login" in page.url or "login" in page.url.lower():
            await browser.close()
            return None

        try:
            await page.wait_for_selector(
                'input[type="url"], input[name="url"], input[placeholder*="URL"], input[placeholder*="url"]',
                timeout=10000
            )
        except PlaywrightTimeout:
            pass

        seletores_input = [
            'input[placeholder*="URL"]', 'input[placeholder*="url"]',
            'input[placeholder*="link"]', 'input[name="url"]',
            'input[type="url"]', '.andes-form-control__field',
        ]

        campo = None
        for sel in seletores_input:
            try:
                el = await page.query_selector(sel)
                if el:
                    campo = el
                    break
            except Exception:
                pass

        link_meli = None
        if campo:
            await campo.fill(url_produto)
            await page.keyboard.press("Enter")
            try:
                await page.wait_for_selector('input[value*="meli.la"], a[href*="meli.la"]', timeout=10000)
            except PlaywrightTimeout:
                pass

            link_meli = await page.evaluate("""
                () => {
                    const inputs = Array.from(document.querySelectorAll('input'));
                    for (const inp of inputs) {
                        if (inp.value && inp.value.includes('meli.la')) return inp.value;
                    }
                    const body = document.body.innerHTML;
                    const m = body.match(/https?:\\/\\/meli\\.la\\/[A-Za-z0-9]+/);
                    return m ? m[0] : null;
                }
            """)

        await browser.close()

    return link_meli


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_sessao()
    else:
        print("Uso:")
        print("  python -m integrations.ml_link_gen setup  → configura sessão (uma vez)")
        print()
        print("  from integrations.ml_link_gen import gerar_link")
        print("  link = gerar_link('https://www.mercadolivre.com.br/...')")
