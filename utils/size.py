import re


_UNIT_ALIASES = {
    "kg": "g",
    "kilo": "g",
    "kilos": "g",
    "kilogramo": "g",
    "kilogramos": "g",
    "g": "g",
    "gr": "g",
    "grs": "g",
    "gramo": "g",
    "gramos": "g",
    "mg": "mg",
    "ml": "ml",
    "l": "ml",
    "lt": "ml",
    "litro": "ml",
    "litros": "ml",
}


def _to_base_unit(value, unit):
    unit = _UNIT_ALIASES[unit]

    if unit == "g":
        return value, "g"

    if unit == "mg":
        return value, "mg"

    if unit == "ml":
        return value, "ml"

    return value, unit


def extract_size(text):
    """Return the first explicit presentation size in normalized units."""
    if not text:
        return None, None

    text = text.lower().replace(",", ".")

    patterns = [
        r"(\d+(?:\.\d+)?)\s*(kg|kilo|kilos|kilogramo|kilogramos)",
        r"(\d+(?:\.\d+)?)\s*(mg)",
        r"(\d+(?:\.\d+)?)\s*(g|gr|grs|gramo|gramos)",
        r"(\d+(?:\.\d+)?)\s*(ml|lt|l|litro|litros)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue

        value = float(match.group(1))
        raw_unit = match.group(2)
        unit = _UNIT_ALIASES[raw_unit]

        if raw_unit in {"kg", "kilo", "kilos", "kilogramo", "kilogramos"}:
            value *= 1000
        elif raw_unit == "l" or raw_unit == "lt" or raw_unit in {"litro", "litros"}:
            value *= 1000

        return _to_base_unit(value, unit)

    return None, None
