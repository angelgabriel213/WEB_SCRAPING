import logging
import os

from flask import Flask, render_template, request

from scrapers.exito import scrape_exito
from scrapers.olimpica import scrape_olimpica
from scrapers.falabella import scrape_falabella
from scrapers.mercadolibre import scrape_mercadolibre
from scrapers.alkosto import scrape_alkosto

from utils.ai_compare import compare_all_products
from utils.cache import get_cached_products, init_cache, save_products


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("buywise")

app = Flask(__name__)
init_cache()

CATALOGO = {
    "Tecnología": ["smartphone", "laptop", "tablet", "iphone", "samsung", "audifonos"],
    "Ropa": ["camisa", "zapatos", "chaqueta", "tenis"],
    "Alimentos": ["arroz", "aceite", "leche", "azucar", "cafe"],
    "Bebidas": ["vino", "cerveza", "whisky", "gaseosa"],
}


def get_products_with_cache(query, store, scraper):
    """Return fresh cache data or scrape the store when cache is missing."""
    cached = get_cached_products(query, store)

    if cached:
        logger.info("%s | CACHE | %s productos", store, len(cached))
        return cached

    try:
        products = scraper(query) or []
        logger.info("%s | SCRAPE | %s productos", store, len(products))

        if products:
            save_products(query, products)

        return products

    except Exception:
        logger.exception("%s | ERROR | scraper failed", store)
        return []


@app.route("/")
def landing():
    return render_template("home.html")


@app.route("/buscar", methods=["GET"])
def home():
    query = (request.args.get("q") or "").strip()

    logger.info("SEARCH | query=%r", query)

    if not query:
        return render_template(
            "index.html",
            productos=[],
            q=query,
            catalogo=CATALOGO,
        )

    stores = [
        ("Exito", lambda value: scrape_exito(value, 1)),
        ("Olimpica", scrape_olimpica),
        ("Falabella", scrape_falabella),
        ("MercadoLibre", scrape_mercadolibre),
        ("Alkosto", scrape_alkosto),
    ]

    products = []

    for store, scraper in stores:
        products.extend(get_products_with_cache(query, store, scraper))

    clean_products = []

    for product in products:
        try:
            price = float(product.get("price", 0))

            if price <= 0 or not product.get("product"):
                continue

            product["price"] = price
            clean_products.append(product)

        except (TypeError, ValueError):
            logger.warning(
                "INVALID_PRODUCT | store=%s | product=%r",
                product.get("store"),
                product.get("product"),
            )

    unique = []
    seen = set()

    for product in clean_products:
        key = (
            product.get("product", "").strip().lower(),
            product.get("store", "").strip().lower(),
        )

        if key not in seen:
            seen.add(key)
            unique.append(product)

    logger.info("SEARCH | unique_products=%s", len(unique))

    try:
        compared = compare_all_products(unique)

    except Exception:
        logger.exception("COMPARISON | AI comparison failed")
        compared = []

    compared.sort(key=lambda item: item["best_price"])

    logger.info("SEARCH | final_results=%s", len(compared))

    return render_template(
        "index.html",
        productos=compared,
        q=query,
        catalogo=CATALOGO,
    )


if __name__ == "__main__":
    app.run(
        debug=os.getenv("FLASK_DEBUG", "true").lower() == "true",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
    )
