import logging
from urllib.parse import quote_plus

import requests

logger = logging.getLogger(__name__)


def _product_url(link):
    if not link:
        return "https://www.olimpica.com"

    if link.startswith("http://") or link.startswith("https://"):
        return link

    return "https://www.olimpica.com/" + link.lstrip("/")


def scrape_olimpica(query):
    resultados = []

    url = (
        "https://www.olimpica.com/"
        "api/catalog_system/pub/products/search/"
        f"?ft={quote_plus(query)}"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }

    try:
        logger.info("Consultando API Olímpica: %s", url)

        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )

        logger.info("Olímpica status: %s", response.status_code)

        if response.status_code not in (200, 206):
            logger.warning("Olímpica API respondió %s", response.status_code)
            return []

        data = response.json()
        logger.info("Olímpica productos recibidos: %s", len(data))

        for item in data:
            try:
                name = (item.get("productName") or "").strip()
                if not name:
                    continue

                items = item.get("items") or []
                if not items:
                    continue

                first_item = items[0]
                sellers = first_item.get("sellers") or []
                if not sellers:
                    continue

                offer = sellers[0].get("commertialOffer") or {}
                price = float(offer.get("Price") or 0)
                available = bool(
                    offer.get("IsAvailableQuantity") or price > 0
                )

                if not available or price <= 0:
                    continue

                images = first_item.get("images") or []
                image = images[0].get("imageUrl", "") if images else ""

                resultados.append({
                    "store": "Olimpica",
                    "product": name,
                    "price": price,
                    "image": image,
                    "url": _product_url(item.get("link", "")),
                    "available": True,
                })

            except (TypeError, ValueError, AttributeError) as exc:
                logger.warning("Olímpica producto inválido: %s", exc)

    except (requests.RequestException, ValueError) as exc:
        logger.exception("Error consultando API Olímpica: %s", exc)
        return []

    final = []
    seen = set()

    for product in resultados:
        key = (
            product["product"].strip().lower(),
            product["price"],
        )
        if key in seen:
            continue
        seen.add(key)
        final.append(product)

    logger.info("TOTAL OLIMPICA: %s", len(final))
    return final
