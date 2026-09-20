from functools import lru_cache
import re

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from utils.size import extract_size


@lru_cache(maxsize=1)
def get_model():
    """Load the embedding model once per application process."""
    return SentenceTransformer("all-MiniLM-L6-v2")


def normalize(text):
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text):
    return normalize(text).split()


def same_size(a, b):
    s1, u1 = extract_size(a)
    s2, u2 = extract_size(b)

    if not s1 or not s2:
        return True

    if u1 != u2:
        return False

    ratio = min(s1, s2) / max(s1, s2)
    return ratio >= 0.90


def common_words(a, b):
    return set(tokenize(a)).intersection(tokenize(b))


def valid_match(a, b, score):
    name1 = normalize(a["product"])
    name2 = normalize(b["product"])

    if len(name1.split()) < 2 or len(name2.split()) < 2:
        return False

    if not same_size(name1, name2):
        return False

    common = common_words(name1, name2)

    if score >= 0.88:
        return True

    if score >= 0.72 and len(common) >= 2:
        return True

    if score >= 0.65 and len(common) >= 3:
        return True

    return False


def compare_all_products(products):
    if not products:
        return []

    clean_products = [
        p for p in products
        if p.get("product")
        and p.get("price")
        and p["price"] > 0
        and p.get("store")
    ]

    if not clean_products:
        return []

    names = [normalize(p["product"]) for p in clean_products]
    embeddings = get_model().encode(names)

    resultados = []

    # Each product gets its own group. A product can be matched with
    # multiple stores instead of being consumed by the first group found.
    for i, product in enumerate(clean_products):
        grupo = [product]
        sims = cosine_similarity([embeddings[i]], embeddings)[0]

        for j, score in enumerate(sims):
            if j == i:
                continue

            other = clean_products[j]

            if other["store"] == product["store"]:
                continue

            if valid_match(product, other, score):
                grupo.append(other)

        # Keep the cheapest listing from each store in this group.
        best_store_prices = {}
        for item in grupo:
            store = item["store"]
            current = best_store_prices.get(store)

            if current is None or item["price"] < current["price"]:
                best_store_prices[store] = item

        grupo = sorted(
            best_store_prices.values(),
            key=lambda item: item["price"]
        )

        best = grupo[0]

        resultados.append({
            "product": best["product"],
            "image": best.get("image", ""),
            "matches": grupo,
            "best_store": best["store"],
            "best_price": best["price"],
        })

    # Remove duplicate groups by the set of product/store pairs.
    unique_results = []
    seen_groups = set()

    for result in resultados:
        group_key = tuple(
            sorted(
                (item["store"], item["product"], item["price"])
                for item in result["matches"]
            )
        )

        if group_key in seen_groups:
            continue

        seen_groups.add(group_key)
        unique_results.append(result)

    return sorted(
        unique_results,
        key=lambda item: (
            len(item["matches"]),
            -item["best_price"],
        ),
        reverse=True,
    )
