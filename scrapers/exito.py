import logging
from urllib.parse import quote_plus

import requests

logger = logging.getLogger(__name__)


def _product_url(link_text):
    if not link_text:
        return ""
    return f"https://www.exito.com/{link_text.strip('/')}/p"


def scrape_exito(query, max_pages=1):
    resultados = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }

    for page in range(max_pages):
        try:
            url = (
                "https://www.exito.com/api/catalog_system/pub/products/search/"
                f"?ft={quote_plus(query)}"
                f"&_from={page * 50}"
                f"&_to={(page * 50) + 49}"
            )

            logger.info("Consultando API Éxito: %s", url)

            response = requests.get(url, headers=headers, timeout=30)
            logger.info("Éxito status: %s", response.status_code)

            if response.status_code not in (200, 206):
                logger.warning("Éxito API respondió %s", response.status_code)
                continue

            data = response.json()
            logger.info("Éxito productos recibidos: %s", len(data))

            for item in data:
                try:
                    name = (item.get("productName") or "").strip()
                    if not name:
                        continue

                    items = item.get("items") or []
                    if not items:
                        continue

                    first_item = items[0]

                    images = first_item.get("images") or []
                    image = images[0].get("imageUrl", "") if images else ""

                    sellers = first_item.get("sellers") or []
                    offer = (
                        sellers[0].get("commertialOffer") or {}
                        if sellers else {}
                    )

                    price = float(offer.get("Price") or 0)
                    available = bool(offer.get("IsAvailableQuantity") or price > 0)

                    if not available or price <= 0:
                        continue

                    resultados.append({
                        "store": "Exito",
                        "product": name,
                        "price": price,
                        "image": image,
                        "url": _product_url(item.get("linkText", "")),
                        "available": True,
                    })

                except (TypeError, ValueError, AttributeError) as exc:
                    logger.warning("Éxito producto inválido: %s", exc)

        except (requests.RequestException, ValueError) as exc:
            logger.exception("Error consultando API Éxito: %s", exc)

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

    logger.info("TOTAL EXITO: %s", len(final))
    return final
