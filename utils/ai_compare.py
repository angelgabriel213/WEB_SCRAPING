from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from utils.size import extract_size
import re

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def normalize(text):

    if not text:
        return ""

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9 ]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def tokenize(text):

    return normalize(text).split()


def same_size(a, b):

    s1, u1 = extract_size(a)
    s2, u2 = extract_size(b)

    # si alguno no tiene tamaño
    # permitir comparación
    if not s1 or not s2:
        return True

    # unidades distintas
    if u1 != u2:
        return False

    ratio = min(s1, s2) / max(s1, s2)

    # permitir diferencia pequeña
    return ratio >= 0.90


def common_words(a, b):

    words1 = set(tokenize(a))
    words2 = set(tokenize(b))

    return words1.intersection(words2)


def valid_match(a, b, score):

    name1 = normalize(a["product"])
    name2 = normalize(b["product"])

    # evitar nombres basura
    if len(name1.split()) < 2:
        return False

    if len(name2.split()) < 2:
        return False

    # tamaños incompatibles
    if not same_size(name1, name2):
        return False

    common = common_words(name1, name2)

    # IA muy fuerte
    if score >= 0.88:
        return True

    # buena coincidencia
    if score >= 0.72 and len(common) >= 2:
        return True

    # electrodomésticos
    if score >= 0.65 and len(common) >= 3:
        return True

    return False


def compare_all_products(products):

    if not products:
        return []

    # limpiar productos inválidos
    clean_products = []

    for p in products:

        if not p.get("product"):
            continue

        if not p.get("price"):
            continue

        if p["price"] <= 0:
            continue

        clean_products.append(p)

    products = clean_products

    if not products:
        return []

    names = [

        normalize(p["product"])

        for p in products
    ]

    embeddings = model.encode(
        names
    )

    usados = set()

    resultados = []

    for i, product in enumerate(products):

        if i in usados:
            continue

        usados.add(i)

        grupo = [product]

        sims = cosine_similarity(

            [embeddings[i]],
            embeddings

        )[0]

        for j, score in enumerate(sims):

            if j == i:
                continue

            if j in usados:
                continue

            other = products[j]

            # evitar misma tienda
            if (
                other["store"]
                == product["store"]
            ):
                continue

            if valid_match(
                product,
                other,
                score
            ):

                grupo.append(other)

                usados.add(j)

        # ordenar por precio

            best_store_prices = {}
            for item in grupo:

                store = item["store"]

                if store not in best_store_prices:

                    best_store_prices[
                        store
                    ] = item

                else:

                    current_price = (
                        best_store_prices[
                            store
                        ]["price"]
                    )

                    if item["price"] < current_price:

                        best_store_prices[
                            store
                        ] = item


            grupo = list(
                best_store_prices.values()
            )


            # ordenar por precio
            grupo = sorted(

                grupo,

                key=lambda x:
                x["price"]
            )

            best = grupo[0]
        resultados.append({

            "product": best["product"],

            "image": best.get(
                "image",
                ""
            ),

            "matches": grupo,

            "best_store": best["store"],

            "best_price": best["price"]
        })

    # ordenar:
    # primero los que tienen más matches
    resultados = sorted(

        resultados,

        key=lambda x: (
            len(x["matches"]),
            -x["best_price"]
        ),

        reverse=True
    )

    return resultados