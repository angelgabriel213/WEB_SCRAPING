import re


def extract_size(text):

    text = text.lower()

    patterns = [

        # 4000 gr
        r'(\d+(?:[\.,]\d+)?)\s*(kg|kilo|kilos)',

        r'(\d+(?:[\.,]\d+)?)\s*(g|gr|grs|gramos)',

        r'(\d+(?:[\.,]\d+)?)\s*(ml|lt|l|litro|litros)',
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:

            value = float(
                match.group(1)
                .replace(",", ".")
            )

            unit = match.group(2)

            # ======================
            # NORMALIZAR KG → G
            # ======================

            if unit in [
                "kg",
                "kilo",
                "kilos"
            ]:

                value *= 1000

                unit = "g"

            # ======================
            # NORMALIZAR L → ML
            # ======================

            if unit in [
                "l",
                "lt",
                "litro",
                "litros"
            ]:

                value *= 1000

                unit = "ml"

            return value, unit

    return None, None