import logging
import re
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


def clean_price(text):
    nums = re.sub(r"[^0-9]", "", text or "")
    return float(nums) if nums else 0.0


def scrape_mercadolibre(query, max_pages=1):
    resultados = []
    encoded_query = quote_plus(query or "")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            try:
                page = context.new_page()
                for page_num in range(max(1, max_pages)):
                    offset = page_num * 48 + 1
                    url = (
                        "https://www.mercadolibre.com.co/jm/search"
                        f"?as_word={encoded_query}&Desde={offset}"
                    )
                    logger.info("Consultando MercadoLibre página %s: %s", page_num + 1, url)
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)

                    try:
                        page.wait_for_selector(".ui-search-results", timeout=15000)
                    except PlaywrightTimeoutError:
                        logger.warning("MercadoLibre: no cargó la lista en página %s", page_num + 1)
                        continue

                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(1500)
                    cards = page.query_selector_all(".ui-search-layout__item")
                    logger.info("MercadoLibre tarjetas encontradas: %s", len(cards))

                    for card in cards:
                        try:
                            titulo_el = card.query_selector(".poly-component__title") or card.query_selector(".ui-search-item__title")
                            if not titulo_el:
                                continue
                            nombre = titulo_el.inner_text().strip()
                            if len(nombre.split()) < 2:
                                continue

                            precio = 0.0
                            promo_el = card.query_selector(
                                ".poly-price__current .andes-money-amount__fraction"
                            )
                            if promo_el:
                                precio = clean_price(promo_el.inner_text())

                            if not precio:
                                for el in card.query_selector_all(".andes-money-amount__fraction"):
                                    parent = el.evaluate(
                                        "el => el.closest('.andes-money-amount')?.className || ''"
                                    )
                                    if "previous" in parent:
                                        continue
                                    candidato = clean_price(el.inner_text())
                                    if candidato > 0:
                                        precio = candidato
                                        break

                            if precio <= 0:
                                continue

                            img_el = card.query_selector("img")
                            imagen = ""
                            if img_el:
                                imagen = img_el.get_attribute("data-src") or img_el.get_attribute("src") or ""
                                if imagen.startswith("//"):
                                    imagen = "https:" + imagen

                            link_el = card.query_selector("a")
                            link = link_el.get_attribute("href") if link_el else ""
                            resultados.append({
                                "store": "MercadoLibre",
                                "product": nombre,
                                "price": precio,
                                "image": imagen,
                                "url": link or "",
                                "available": True,
                            })
                        except Exception:
                            logger.exception("MercadoLibre error procesando tarjeta")
            finally:
                browser.close()
    except Exception:
        logger.exception("Error consultando MercadoLibre")
        return []

    unicos = []
    vistos = set()
    for product in resultados:
        key = (product["product"].strip().lower(), product["price"])
        if key not in vistos:
            vistos.add(key)
            unicos.append(product)

    logger.info("TOTAL MERCADOLIBRE: %s", len(unicos))
    return unicos
