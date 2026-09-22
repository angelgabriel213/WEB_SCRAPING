from playwright.sync_api import sync_playwright
import re


def clean_price(text):
    nums = re.sub(r"[^0-9]", "", text)
    if not nums:
        return 0
    return float(nums)


def scrape_mercadolibre(query, max_pages=1):

    resultados = []

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        page = context.new_page()

        for page_num in range(max_pages):

            offset = (page_num * 48) + 1

            url = (
                f"https://www.mercadolibre.com.co/jm/search"
                f"?as_word={query}&Desde={offset}"
            )

            print(f"\nPágina {page_num + 1}: {url}")

            page.goto(url, timeout=60000)

            try:
                page.wait_for_selector(
                    ".ui-search-results",
                    timeout=15000
                )
            except:
                print("No cargó la lista, tomando screenshot...")
                page.screenshot(
                    path=f"ml_debug_{page_num}.png"
                )
                continue

            page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight)"
            )
            page.wait_for_timeout(2000)

            cards = page.query_selector_all(
                ".ui-search-layout__item"
            )

            print(f"Tarjetas encontradas: {len(cards)}")

            for card in cards:

                try:

                    # nombre
                    titulo_el = card.query_selector(
                        ".poly-component__title"
                    )
                    if not titulo_el:
                        titulo_el = card.query_selector(
                            ".ui-search-item__title"
                        )
                    if not titulo_el:
                        continue

                    nombre = titulo_el.inner_text().strip()

                    if len(nombre.split()) < 2:
                        continue

                    # precio promocion primero
                    # ML marca el precio tachado con
                    # andes-money-amount--previous
                    # y el precio real/oferta sin esa clase
                    precio = 0

                    # buscar precio de promocion
                    promo_el = card.query_selector(
                        ".poly-price__current "
                        ".andes-money-amount__fraction"
                    )

                    if promo_el:
                        precio = clean_price(
                            promo_el.inner_text()
                        )

                    # fallback: cualquier precio
                    # que no esté tachado
                    if not precio:
                        todos = card.query_selector_all(
                            ".andes-money-amount__fraction"
                        )
                        for el in todos:
                            parent = el.evaluate(
                                "el => el.closest("
                                "'.andes-money-amount')"
                                ".className"
                            )
                            if "previous" in parent:
                                continue
                            precio = clean_price(
                                el.inner_text()
                            )
                            if precio > 1000:
                                break

                    if precio <= 1000:
                        continue

                    # imagen
                    img_el = card.query_selector("img")
                    imagen = ""
                    if img_el:
                        imagen = (
                            img_el.get_attribute("data-src")
                            or img_el.get_attribute("src")
                            or ""
                        )
                        if imagen.startswith("//"):
                            imagen = "https:" + imagen

                    # url
                    link_el = card.query_selector("a")
                    link = ""
                    if link_el:
                        link = link_el.get_attribute("href") or ""

                    resultados.append({
                        "store": "MercadoLibre",
                        "product": nombre,
                        "price": precio,
                        "image": imagen,
                        "url": link,
                    })

                    print(f"✅ {nombre} - ${precio}")

                except Exception as e:
                    print(f"Error en tarjeta: {e}")
                    continue

        browser.close()

    # eliminar duplicados
    vistos = set()
    unicos = []

    for p in resultados:
        key = (p["product"], p["price"])
        if key in vistos:
            continue
        vistos.add(key)
        unicos.append(p)

    print(f"\nTOTAL MERCADOLIBRE: {len(unicos)}")
    return unicos