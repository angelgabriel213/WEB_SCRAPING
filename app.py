import logging
import os

from flask import Flask, render_template, request

from scrapers.exito import scrape_exito
from scrapers.olimpica import scrape_olimpica
from scrapers.falabella import scrape_falabella
from scrapers.mercadolibre import scrape_mercadolibre
from scrapers.alkosto import scrape_alkosto

from services.search_service import StoreScraper, search_store
from services.product_service import process_products


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("buywise")

app = Flask(__name__)

CATALOGO = {
    "Tecnología": ["smartphone", "laptop", "tablet", "iphone", "samsung", "audifonos"],
    "Ropa": ["camisa", "zapatos", "chaqueta", "tenis"],
    "Alimentos": ["arroz", "aceite", "leche", "azucar", "cafe"],
    "Bebidas": ["vino", "cerveza", "whisky", "gaseosa"],
}


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
        products.extend(
            search_store(query, StoreScraper(name=store, scraper=scraper))
        )

    compared = process_products(products)
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
