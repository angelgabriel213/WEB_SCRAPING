from flask import Flask, render_template, request

from scrapers.exito import scrape_exito
from scrapers.olimpica import scrape_olimpica
from scrapers.falabella import scrape_falabella
from scrapers.mercadolibre import scrape_mercadolibre
from scrapers.alkosto import scrape_alkosto

from utils.ai_compare import compare_all_products
from utils.cache import get_cached_products, init_cache, save_products


app = Flask(__name__)

# Initialize the local cache when the application process starts.
init_cache()

CATALOGO = {
    "Tecnología": ["smartphone", "laptop", "tablet", "iphone", "samsung", "audifonos"],
    "Ropa": ["camisa", "zapatos", "chaqueta", "tenis"],
    "Alimentos": ["arroz", "aceite", "leche", "azucar", "cafe"],
    "Bebidas": ["vino", "cerveza", "whisky", "gaseosa"],
}


def get_products_with_cache(query, store, scraper):
    """Use fresh cached results when available; scrape only on cache miss."""
    cached = get_cached_products(query, store)

    if cached:
        print(f"♻️ CACHE {store}: {len(cached)} productos")
        return cached

    try:
        products = scraper(query)
        print(f"🌐 SCRAPE {store}: {len(products)} productos")
        if products:
            save_products(query, products)
        return products
    except Exception as exc:
        print(f"❌ Error {store}: {exc}")
        return []


@app.route("/")
def landing():
    return render_template("home.html")


@app.route("/buscar", methods=["GET"])
def home():
    q = (request.args.get("q") or "").strip()

    print(f"\n🔍 Buscando: {q}")

    if not q:
        return render_template(
            "index.html",
            productos=[],
            q=q,
            catalogo=CATALOGO,
        )

    stores = [
        ("Exito", lambda value: scrape_exito(value, 1)),
        ("Olimpica", scrape_olimpica),
        ("Falabella", scrape_falabella),
        ("MercadoLibre", scrape_mercadolibre),
        ("Alkosto", scrape_alkosto),
    ]

    productos = []

    for store, scraper in stores:
        products = get_products_with_cache(q, store, scraper)
        productos.extend(products)

    clean_products = []

    for product in productos:
        try:
            product["price"] = float(product.get("price", 0))
            if product["price"] <= 0 or not product.get("product"):
                continue
            clean_products.append(product)
        except (TypeError, ValueError):
            continue

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

    print(f"Productos únicos: {len(unique)}")

    try:
        comparados = compare_all_products(unique)
    except Exception as exc:
        print(f"❌ Error IA: {exc}")
        comparados = []

    comparados.sort(key=lambda item: item["best_price"])

    print(f"✅ Productos finales: {len(comparados)}")

    return render_template(
        "index.html",
        productos=comparados,
        q=q,
        catalogo=CATALOGO,
    )


if __name__ == "__main__":
    init_cache()

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
    )
