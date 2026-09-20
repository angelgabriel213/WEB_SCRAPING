import os
import sqlite3
from datetime import datetime, timedelta, timezone


DB_PATH = os.getenv("BUYWISE_DB_PATH", "buywise_cache.db")
CACHE_TTL_MINUTES = int(os.getenv("BUYWISE_CACHE_TTL_MINUTES", "30"))


def _connect():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _normalize_query(query):
    return " ".join((query or "").strip().lower().split())


def init_cache():
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS products_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                store TEXT NOT NULL,
                product TEXT NOT NULL,
                price REAL NOT NULL,
                image TEXT,
                product_url TEXT,
                fetched_at TEXT NOT NULL,
                UNIQUE(query, store, product, product_url)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_products_cache_query_store
            ON products_cache(query, store)
            """
        )


def get_cached_products(query, store):
    normalized_query = _normalize_query(query)
    cutoff = datetime.now(timezone.utc) - timedelta(
        minutes=CACHE_TTL_MINUTES
    )

    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT product, price, image, product_url, store
            FROM products_cache
            WHERE query = ?
              AND store = ?
              AND fetched_at >= ?
            """,
            (
                normalized_query,
                store,
                cutoff.isoformat(),
            ),
        ).fetchall()

    return [
        {
            "product": row["product"],
            "price": row["price"],
            "image": row["image"] or "",
            "url": row["product_url"] or "",
            "store": row["store"],
        }
        for row in rows
    ]


def save_products(query, products):
    normalized_query = _normalize_query(query)
    if not normalized_query or not products:
        return

    store = products[0].get("store")
    if not store:
        return

    fetched_at = datetime.now(timezone.utc).isoformat()

    with _connect() as connection:
        connection.execute(
            "DELETE FROM products_cache WHERE query = ? AND store = ?",
            (normalized_query, store),
        )

        for product in products:
            if not product.get("product") or not product.get("price"):
                continue

            connection.execute(
                """
                INSERT OR REPLACE INTO products_cache
                (query, store, product, price, image, product_url, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized_query,
                    store,
                    product["product"],
                    float(product["price"]),
                    product.get("image", ""),
                    product.get("url", ""),
                    fetched_at,
                ),
            )


def clear_cache():
    with _connect() as connection:
        connection.execute("DELETE FROM products_cache")
