from flask import Flask, render_template, request

# =========================
# SCRAPERS
# =========================

from scrapers.exito import scrape_exito
from scrapers.olimpica import scrape_olimpica
from scrapers.falabella import scrape_falabella
from scrapers.mercadolibre import scrape_mercadolibre
from scrapers.alkosto import scrape_alkosto   # ✅ nuevo

# =========================
# IA COMPARADOR
# =========================

from utils.ai_compare import (
    compare_all_products
)

app = Flask(__name__)

# =========================
# CATÁLOGO
# =========================

CATALOGO = {

    "Tecnología": [
        "smartphone",
        "laptop",
        "tablet",
        "iphone",
        "samsung",
        "audifonos"
    ],

    "Ropa": [
        "camisa",
        "zapatos",
        "chaqueta",
        "tenis"
    ],

    "Alimentos": [
        "arroz",
        "aceite",
        "leche",
        "azucar",
        "cafe"
    ],

    "Bebidas": [
        "vino",
        "cerveza",
        "whisky",
        "gaseosa"
    ]
}


# =========================
# HOME
# =========================
@app.route("/")
def landing():

    return render_template(
        "home.html"
    )  

@app.route("/buscar", methods=["GET"])
def home():

    q = request.args.get("q")

    if not q:
        q = ""

    q = q.strip()

    print(f"\n🔍 Buscando: {q}")

    # =========================
    # SCRAPERS
    # =========================

    exito_products = []
    olimpica_products = []
    falabella_products = []
    mercadolibre_products = []
    alkosto_products = []   # ✅ nuevo


    # =========================
    # ÉXITO
    # =========================

    try:

        exito_products = scrape_exito(
            q,
            1
        )

        print(
            f"TOTAL EXITO: "
            f"{len(exito_products)}"
        )

    except Exception as e:

        print(
            "❌ Error Exito:",
            e
        )


    # =========================
    # OLÍMPICA
    # =========================

    try:

        olimpica_products = scrape_olimpica(q)

        print(
            f"TOTAL OLIMPICA: "
            f"{len(olimpica_products)}"
        )

    except Exception as e:

        print(
            "❌ Error Olimpica:",
            e
        )


    # =========================
    # FALABELLA
    # =========================

    try:

        falabella_products = scrape_falabella(q)

        print(
            f"TOTAL FALABELLA: "
            f"{len(falabella_products)}"
        )

    except Exception as e:

        print(
            "❌ Error Falabella:",
            e
        )


    # =========================
    # MERCADO LIBRE
    # =========================

    try:

        mercadolibre_products = scrape_mercadolibre(q)

        print(
            f"TOTAL MERCADO LIBRE: "
            f"{len(mercadolibre_products)}"
        )

    except Exception as e:

        print(
            "❌ Error Mercado Libre:",
            e
        )


    # =========================
    # ALKOSTO
    # =========================

    try:

        alkosto_products = scrape_alkosto(q)

        print(
            f"TOTAL ALKOSTO: "
            f"{len(alkosto_products)}"
        )

    except Exception as e:

        print(
            "❌ Error Alkosto:",
            e
        )


    # =========================
    # UNIR PRODUCTOS
    # =========================

    productos = (

        exito_products +

        olimpica_products +

        falabella_products +

        mercadolibre_products +

        alkosto_products
    )


    # =========================
    # LIMPIAR PRECIOS
    # =========================

    clean_products = []

    for p in productos:

        try:

            p["price"] = float(
                p.get("price", 0)
            )

            if p["price"] <= 0:
                continue

            if not p.get("product"):
                continue

            clean_products.append(p)

        except:
            pass


    # =========================
    # ELIMINAR DUPLICADOS
    # =========================

    unique = []

    seen = set()

    for p in clean_products:

        key = (

            p.get(
                "product",
                ""
            ).lower(),

            p.get(
                "store",
                ""
            )
        )

        if key not in seen:

            seen.add(key)

            unique.append(p)


    print(
        f"Productos únicos: "
        f"{len(unique)}"
    )


    # =========================
    # IA COMPARACIÓN
    # =========================

    try:

        comparados = compare_all_products(
            unique
        )

    except Exception as e:

        print(
            "❌ Error IA:",
            e
        )

        comparados = []


    # =========================
    # ORDENAR
    # =========================

    comparados = sorted(

        comparados,

        key=lambda x: x["best_price"]
    )


    print(
        f"✅ Productos finales: "
        f"{len(comparados)}"
    )


    return render_template(

        "index.html",

        productos=comparados,

        q=q,

        catalogo=CATALOGO
    )


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="0.0.0.0",

        port=5000
    )