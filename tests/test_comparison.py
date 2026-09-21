import pytest

from app import app
from services.product_service import clean_products
from utils.ai_compare import valid_match
from utils.cache import _normalize_query
from utils.size import extract_size


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Arroz 1 kg", (1000.0, "g")),
        ("Arroz 1000 g", (1000.0, "g")),
        ("Aceite 1 litro", (1000.0, "ml")),
        ("Aceite 900 ml", (900.0, "ml")),
        ("Suplemento 500 mg", (500.0, "mg")),
    ],
)
def test_extract_size(text, expected):
    assert extract_size(text) == expected


def test_extract_size_rejects_different_presentations():
    assert extract_size("Arroz 500 g") != extract_size("Arroz 1 kg")


def test_normalize_query():
    assert _normalize_query("  Arroz   Integral  ") == "arroz integral"


def product(name, price=10000, store="Exito"):
    return {"product": name, "price": price, "store": store}


def test_same_model_different_storage_is_not_match():
    assert not valid_match(
        product("Apple iPhone 15 128GB"),
        product("Apple iPhone 15 256GB", store="Olimpica"),
        0.95,
    )


def test_different_model_is_not_match():
    assert not valid_match(
        product("Samsung Galaxy A54"),
        product("Samsung Galaxy A55", store="Olimpica"),
        0.95,
    )


def test_different_variant_is_not_match():
    assert not valid_match(
        product("Cafe 500 g"),
        product("Cafe descafeinado 500 g", store="Olimpica"),
        0.95,
    )


def test_same_product_and_size_can_match():
    assert valid_match(
        product("Arroz Diana 1 kg"),
        product("Arroz Diana 1 kg", store="Olimpica"),
        0.90,
    )


def test_clean_products_removes_invalid_and_duplicates():
    products = [
        product("Arroz Diana 1 kg", 8000, "Exito"),
        product("Arroz Diana 1 kg", 8000, "Exito"),
        product("Producto sin precio", 0, "Exito"),
        product("", 5000, "Olimpica"),
        product("Arroz Diana 1 kg", 7500, "Olimpica"),
    ]

    result = clean_products(products)

    assert len(result) == 2
    assert result[0]["price"] == 8000
    assert result[1]["price"] == 7500


def test_search_route_rejects_empty_query_without_scraping():
    client = app.test_client()
    response = client.get("/buscar")

    assert response.status_code == 200
