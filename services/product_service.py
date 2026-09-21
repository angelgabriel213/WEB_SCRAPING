import logging

from utils.ai_compare import compare_all_products


logger = logging.getLogger("buywise.products")


def clean_products(products):
    clean = []
    seen = set()

    for product in products:
        try:
            price = float(product.get("price", 0))

            if price <= 0 or not product.get("product"):
                continue

            product["price"] = price

            key = (
                product.get("product", "").strip().lower(),
                product.get("store", "").strip().lower(),
            )

            if key in seen:
                continue

            seen.add(key)
            clean.append(product)

        except (TypeError, ValueError):
            logger.warning(
                "INVALID_PRODUCT | store=%s | product=%r",
                product.get("store"),
                product.get("product"),
            )

    return clean


def process_products(products):
    clean = clean_products(products)
    logger.info("PRODUCTS | unique_products=%s", len(clean))

    try:
        results = compare_all_products(clean)
    except Exception:
        logger.exception("COMPARISON | AI comparison failed")
        return []

    results.sort(key=lambda item: item["best_price"])
    return results
