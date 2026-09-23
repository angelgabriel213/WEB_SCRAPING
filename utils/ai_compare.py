from functools import lru_cache
import re

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from utils.size import extract_size


# Words that describe variants rather than the base product.
VARIANT_GROUPS = {
    "storage": {
        "32gb", "64gb", "128gb", "256gb", "512gb", "1tb", "2tb",
    },
    "ram": {
        "2gb", "3gb", "4gb", "6gb", "8gb", "12gb", "16gb", "24gb", "32gb",
    },
    "edition": {
        "pro", "plus", "ultra", "max", "mini", "lite", "air", "fe",
        "se", "edge", "note", "classic", "premium",
    },
    "diet": {
        "light", "zero", "sin", "azucar", "azúcar", "descafeinado",
        "descremado", "deslactosada", "deslactosado", "integral",
    },
}


@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


def normalize(text):
    if not text:
        return ""

    text = text.lower()
    text = text.replace("á", "a").replace("é", "e").replace("í", "i")
    text = text.replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text):
    return set(normalize(text).split())


def extract_variant_tokens(text):
    """Return meaningful variant tokens such as model tiers and capacities."""
    tokens = tokenize(text)
    variants = set()

    for group in VARIANT_GROUPS.values():
        variants.update(tokens.intersection(group))

    # Generic model/capacity tokens such as A54, S24, X5, etc.
    for token in tokens:
        if re.search(r"\d", token) and re.search(r"[a-z]", token):
            variants.add(token)

    return variants


def conflicting_variants(a, b):
    """Reject clearly different variants when both names expose them."""
    variants_a = extract_variant_tokens(a)
    variants_b = extract_variant_tokens(b)

    if not variants_a or not variants_b:
        return False

    # Exact variant agreement is required when both products expose
    # the same category of differentiating token.
    for group in VARIANT_GROUPS.values():
        a_group = variants_a.intersection(group)
        b_group = variants_b.intersection(group)

        if a_group and b_group and a_group.isdisjoint(b_group):
            return True

        # Some variants are meaningful even when only one listing exposes
        # the differentiator (for example regular coffee vs decaf).
    for variant_name in ("diet", "edition"):
        a_group = variants_a.intersection(VARIANT_GROUPS[variant_name])
        b_group = variants_b.intersection(VARIANT_GROUPS[variant_name])
        if (a_group or b_group) and a_group != b_group:
            return True

    # Alphanumeric model references should not silently cross-match.
    model_a = {
        token for token in variants_a
        if re.search(r"[a-z]", token) and re.search(r"\d", token)
    }
    model_b = {
        token for token in variants_b
        if re.search(r"[a-z]", token) and re.search(r"\d", token)
    }

    if model_a and model_b and model_a.isdisjoint(model_b):
        return True

    return False


def same_size(a, b):
    s1, u1 = extract_size(a)
    s2, u2 = extract_size(b)

    if not s1 or not s2:
        return True

    if u1 != u2:
        return False

    ratio = min(s1, s2) / max(s1, s2)
    return ratio >= 0.95


def common_words(a, b):
    return tokenize(a).intersection(tokenize(b))


def valid_match(a, b, score):
    name1 = normalize(a["product"])
    name2 = normalize(b["product"])

    if len(name1.split()) < 2 or len(name2.split()) < 2:
        return False

    if not same_size(name1, name2):
        return False

    if conflicting_variants(name1, name2):
        return False

    common = common_words(name1, name2)

    # High semantic similarity still has to pass the hard rules above.
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

        best_store_prices = {}
        for item in grupo:
            store = item["store"]
            current = best_store_prices.get(store)

            if current is None or item["price"] < current["price"]:
                best_store_prices[store] = item

        grupo = sorted(
            best_store_prices.values(),
            key=lambda item: item["price"],
        )

        best = grupo[0]

        resultados.append({
            "product": best["product"],
            "image": best.get("image", ""),
            "matches": grupo,
            "best_store": best["store"],
            "best_price": best["price"],
        })

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

    # Show groups with more store matches first; within the same
    # coverage level, prefer the lower best price.
    return sorted(
        unique_results,
        key=lambda item: (
            -len(item["matches"]),
            item["best_price"],
        ),
    )
