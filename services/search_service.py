import logging
from dataclasses import dataclass
from typing import Callable

from utils.cache import get_cached_products, save_products


logger = logging.getLogger("buywise.search")


@dataclass(frozen=True)
class StoreScraper:
    name: str
    scraper: Callable


def search_store(query: str, store: StoreScraper):
    cached = get_cached_products(query, store.name)

    if cached:
        logger.info("%s | CACHE | %s productos", store.name, len(cached))
        return cached

    try:
        products = store.scraper(query) or []
        logger.info("%s | SCRAPE | %s productos", store.name, len(products))

        if products:
            save_products(query, products)

        return products
    except Exception:
        logger.exception("%s | ERROR | scraper failed", store.name)
        return []
