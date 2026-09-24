import logging
import re
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


def clean_price(text):
    nums = re.sub(r"[^0-9]", "", text or "")
    return float(nums) if nums else 0.0


def scrape_falabella(query):
    productos = []
    encoded_query = quote_plus(query or "")
    url = f"https://www.falabella.com.co/falabella-co/search?Ntt={encoded_query}"

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
                def block_resources(route):
                    if route.request.resource_type in {"font", "media", "websocket"}:
                        route.abort()
                    else:
                        route.continue_()

                context.route("**/*", block_resources)
                page = context.new_page()
                logger.info("Consultando Falabella: %s", url)
                page.goto(url, wait_until="domcontentloaded", timeout=60000)

                try:
                    page.wait_for_selector("[data-testid='result-pod']", timeout=20000)
                except PlaywrightTimeoutError:
                    try:
                        page.wait_for_selector(".pod-subTitle, .pod-title", timeout=10000)
                    except PlaywrightTimeoutError:
                        logger.warning("Falabella: no se encontraron productos")
                        return []

                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                page.wait_for_timeout(1500)

                cards = page.query_selector_all("[data-testid='result-pod']")
                if not cards:
                    cards = page.query_selector_all(".pod")
                logger.info("Falabella tarjetas encontradas: %s", len(cards))

                for card in cards:
                    try:
                        nombre_el = (
                            card.query_selector("[data-testid='pod-displaySubTitle']")
                            or card.query_selector(".pod-subTitle")
                            or card.query_selector(".pod-title")
                        )
                        if not nombre_el:
                            continue
                        nombre = nombre_el.inner_text().strip()
                        if len(nombre.split()) < 2:
                            continue

                        precio_el = (
                            card.query_selector("[data-testid='pod-prices-0-price-0']")
                            or card.query_selector(".copy10.primary")
                            or card.query_selector(".prices-0")
                            or card.query_selector("[class*='price']")
                        )
                        if not precio_el:
                            continue
                        precio = clean_price(precio_el.inner_text())
                        if precio <= 0:
                            continue

                        img_el = card.query_selector("img")
                        imagen = ""
                        if img_el:
                            imagen = img_el.get_attribute("src") or img_el.get_attribute("data-src") or ""

                        link = url
                        link_el = card.query_selector("a")
                        if link_el:
                            href = link_el.get_attribute("href") or ""
                            if href.startswith("http"):
                                link = href
                            elif href.startswith("/"):
                                link = f"https://www.falabella.com.co{href}"

                        productos.append({
                            "product": nombre,
                            "price": precio,
                            "store": "Falabella",
                            "url": link,
                            "image": imagen,
                            "available": True,
                        })
                    except Exception:
                        logger.exception("Falabella error procesando tarjeta")
            finally:
                browser.close()
    except Exception:
        logger.exception("Error consultando Falabella")
        return []

    unicos = []
    vistos = set()
    for product in productos:
        key = (product["product"].strip().lower(), product["price"])
        if key not in vistos:
            vistos.add(key)
            unicos.append(product)

    logger.info("TOTAL FALABELLA: %s", len(unicos))
    return unicos
