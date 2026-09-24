import logging
import re
from urllib.parse import quote_plus

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

logger = logging.getLogger(__name__)


def _absolute_url(value):
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return "https://www.alkosto.com" + (value if value.startswith("/") else f"/{value}")


def scrape_alkosto(query):
    resultados = []
    encoded_query = quote_plus(query or "")
    url = f"https://www.alkosto.com/search?text={encoded_query}"
    logger.info("Consultando Alkosto: %s", url)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            try:
                page = browser.new_page()
                page.route(
                    "**/*",
                    lambda route: route.abort()
                    if route.request.resource_type in {"image", "font", "media"}
                    else route.continue_(),
                )
                page.goto(url, wait_until="domcontentloaded", timeout=30000)

                selectors = [".js-product-item", ".product-item", ".ais-Hits-item", "[data-product-name]"]
                productos = None
                for selector in selectors:
                    try:
                        page.wait_for_selector(selector, timeout=5000)
                        locator = page.locator(selector)
                        if locator.count() > 0:
                            productos = locator
                            logger.info("Alkosto selector usado: %s", selector)
                            break
                    except PlaywrightTimeoutError:
                        continue

                if productos is None:
                    logger.warning("Alkosto: no se encontraron productos")
                    return []

                total = productos.count()
                logger.info("Alkosto productos encontrados: %s", total)
                for i in range(total):
                    try:
                        html = productos.nth(i).inner_html()
                        name = ""
                        for pattern in (r'title="([^"]+)"', r'alt="([^"]+)"', r'productName":"([^"]+)"'):
                            match = re.search(pattern, html)
                            if match:
                                name = match.group(1).strip()
                                break
                        if not name:
                            continue

                        prices = re.findall(r"\$[\d\.\,]+", html)
                        if not prices:
                            continue
                        price_text = re.sub(r"[^\d]", "", prices[0])
                        price = float(price_text) if price_text else 0.0
                        if price <= 0:
                            continue

                        image = ""
                        for pattern in (r'<img[^>]+src="([^"]+)"', r'<img[^>]+data-src="([^"]+)"'):
                            match = re.search(pattern, html)
                            if match:
                                image = _absolute_url(match.group(1))
                                break

                        match = re.search(r'<a[^>]+href="([^"]+)"', html)
                        product_url = _absolute_url(match.group(1)) if match else ""
                        resultados.append({
                            "store": "Alkosto",
                            "product": name,
                            "price": price,
                            "image": image,
                            "url": product_url,
                            "available": True,
                        })
                    except Exception:
                        logger.exception("Alkosto error procesando producto %s", i)
            finally:
                browser.close()
    except Exception:
        logger.exception("Error consultando Alkosto")
        return []

    unicos = []
    vistos = set()
    for product in resultados:
        key = (product["product"].strip().lower(), product["price"])
        if key not in vistos:
            vistos.add(key)
            unicos.append(product)
    logger.info("TOTAL ALKOSTO: %s", len(unicos))
    return unicos
