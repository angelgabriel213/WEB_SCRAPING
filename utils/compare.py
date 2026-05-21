from rapidfuzz import fuzz

from utils.normalize import normalize
from utils.size import extract_size


def compare_products(
    exito_products,
    olimpica_products
):

    comparados = []

    for exito in exito_products:

        best_match = None

        best_score = 0

        exito_name = normalize(
            exito["product"]
        )

        exito_size, exito_unit = (
            extract_size(
                exito["product"]
            )
        )

        for olimpica in olimpica_products:

            olimpica_name = normalize(
                olimpica["product"]
            )

            olimpica_size, olimpica_unit = (
                extract_size(
                    olimpica["product"]
                )
            )

            # validar unidad
            if (
                exito_unit
                and olimpica_unit
                and exito_unit != olimpica_unit
            ):
                continue

            # validar gramaje
            if (
                exito_size
                and olimpica_size
            ):

                diff = abs(
                    exito_size - olimpica_size
                )

                max_size = max(
                    exito_size,
                    olimpica_size
                )

                # permitir máximo 20%
                if diff > (max_size * 0.2):
                    continue

            score = fuzz.token_sort_ratio(
                exito_name,
                olimpica_name
            )

            if score > best_score:

                best_score = score

                best_match = olimpica

        if best_score >= 45 and best_match:

            exito_price = float(
                exito["price"]
            )

            olimpica_price = float(
                best_match["price"]
            )

            cheaper_store = (
                "Exito"
                if exito_price < olimpica_price
                else "Olimpica"
            )

            diff = abs(
                exito_price - olimpica_price
            )

            comparados.append({

                "product": exito["product"],

                "image": exito["image"],

                "exito_price": exito_price,

                "olimpica_price": olimpica_price,

                "difference": diff,

                "best_store": cheaper_store,

                "exito_url": exito["url"],

                "olimpica_url": best_match["url"]
            })

    return comparados