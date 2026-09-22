from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from urllib.parse import quote_plus
import re


def scrape_alkosto(query):

    resultados = []

    url = (
        "https://www.alkosto.com/search"
        f"?text={quote_plus(query)}"
    )

    logger.info("Consultando Alkosto: %s", url)

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True
            )

            page = browser.new_page()

            # Bloquear recursos pesados
            page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type
                    in ["image", "font", "media"]
                    else route.continue_()
                )
            )

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            selectors = [

                ".js-product-item",
                ".product-item",
                ".ais-Hits-item",
                '[data-product-name]'

            ]

            productos = None

            for selector in selectors:

                try:

                    page.wait_for_selector(
                        selector,
                        timeout=5000
                    )

                    test = page.locator(
                        selector
                    )

                    if test.count() > 0:

                        productos = test

                        logger.info("Alkosto selector usado: %s", selector)

                        break

                except PlaywrightTimeoutError:
                    continue

            if productos is None:

                logger.warning("Alkosto: no se encontraron productos")

                browser.close()

                return []


            total = productos.count()

            print(
                "Productos encontrados:",
                total
            )


            # =====================
            # Copiar HTML completo
            # =====================

            cards = []

            for i in range(total):

                try:

                    cards.append(

                        productos.nth(
                            i
                        ).inner_html()

                    )

                except:
                    pass


            # =====================
            # Procesar tarjetas
            # =====================

            for html in cards:

                try:

                    # ----------------
                    # Nombre
                    # ----------------

                    name = ""

                    patterns = [

                        r'title="([^"]+)"',
                        r'alt="([^"]+)"',
                        r'productName":"([^"]+)"'

                    ]

                    for pattern in patterns:

                        m = re.search(
                            pattern,
                            html
                        )

                        if m:

                            name = m.group(
                                1
                            )

                            break

                    if not name:
                        continue


                    # ----------------
                    # Precio
                    # ----------------

                    price = ""

                    precios = re.findall(
                        r'\$[\d\.\,]+',
                        html
                    )

                    if precios:

                        price = precios[0]

                        price = re.sub(
                            r"[^\d]",
                            "",
                            price
                        )

                    if not price:
                        continue


                    # ----------------
                    # Imagen
                    # ----------------

                    image = ""

                    patterns = [

                        r'<img[^>]+src="([^"]+)"',
                        r'<img[^>]+data-src="([^"]+)"'

                    ]

                    for pattern in patterns:

                        m = re.search(
                            pattern,
                            html
                        )

                        if m:

                            image = m.group(
                                1
                            )

                            break


                    # ----------------
                    # URL
                    # ----------------

                    product_url = ""

                    m = re.search(
                        r'<a[^>]+href="([^"]+)"',
                        html
                    )

                    if m:

                        product_url = m.group(
                            1
                        )

                        if not product_url.startswith(
                            "http"
                        ):

                            product_url = (
                                "https://www.alkosto.com"
                                + product_url
                            )


                    resultados.append({

                        "store": "Alkosto",

                        "product": name,

                        "price": float(
                            price
                        ),

                        "image": image,

                        "url": product_url
                    })

                    logger.info("Alkosto producto: %s - $%s", name, price)

                except Exception as e:

                    logger.warning("Alkosto error procesando producto: %s", e)

            browser.close()

    except Exception as e:

        logger.exception("Error Alkosto")

    logger.info("TOTAL ALKOSTO: %s", len(resultados))

    return resultados