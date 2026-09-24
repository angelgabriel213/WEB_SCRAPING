import os
import sqlite3
from datetime import datetime, timedelta, timezone

DB_PATH = os.getenv("BUYWISE_DB_PATH", "buywise_cache.db")
CACHE_TTL_MINUTES = int(os.getenv("BUYWISE_CACHE_TTL_MINUTES", "30"))


def _connect():
    parent = os.path.dirname(DB_PATH)
    if parent:
        os.makedirs(parent, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _normalize_query(query):
    return " ".join((query or "").strip().lower().split())


def init_cache():
    with _connect() as connection:
        connection.execute("""
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
        """)
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_products_cache_query_store
            ON products_cache(query, store)
        """)


def get_cached_products(query, store):
    normalized_query = _normalize_query(query)
    if not normalized_query or not store:
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=CACHE_TTL_MINUTES)
    init_cache()
    with _connect() as connection:
        rows = connection.execute(
            """SELECT product, price, image, product_url, store
               FROM products_cache
               WHERE query = ? AND store = ? AND fetched_at >= ?""",
            (normalized_query, store, cutoff.isoformat()),
        ).fetchall()
    return [
        {"product": row["product"], "price": row["price"], "image": row["image"] or "", "url": row["product_url"] or "", "store": row["store"]}
        for row in rows
    ]


def save_products(query, products):
    normalized_query = _normalize_query(query)
    if not normalized_query or not products:
        return
    fetched_at = datetime.now(timezone.utc).isoformat()
    by_store = {}
    for product in products:
        store = (product.get("store") or "").strip()
        if store:
            by_store.setdefault(store, []).append(product)

    init_cache()
    with _connect() as connection:
        for store, store_products in by_store.items():
            connection.execute("DELETE FROM products_cache WHERE query = ? AND store = ?", (normalized_query, store))
            for product in store_products:
                name = (product.get("product") or "").strip()
                try:
                    price = float(product.get("price", 0))
                except (TypeError, ValueError):
                    continue
                if not name or price <= 0:
                    continue
                connection.execute(
                    """INSERT OR REPLACE INTO products_cache
                       (query, store, product, price, image, product_url, fetched_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (normalized_query, store, name, price, product.get("image", ""), product.get("url", ""), fetched_at),
                )


def clear_cache():
    init_cache()
    with _connect() as connection:
        connection.execute("DELETE FROM products_cache")
