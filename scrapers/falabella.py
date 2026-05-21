from playwright.sync_api import sync_playwright
import re


def clean_price(text):
    nums = re.sub(r"[^0-9]", "", text)
    if not nums:
        return 0
    return float(nums)


def scrape_falabella(query):

    productos = []

    try:
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

            # bloquear recursos pesados para cargar más rápido
            def block_resources(route):
                if route.request.resource_type in [
                    "font",
                    "media",
                    "websocket"
                ]:
                    route.abort()
                else:
                    route.continue_()

            context.route("**/*", block_resources)

            page = context.new_page()

            url = (
                f"https://www.falabella.com.co/falabella-co/search"
                f"?Ntt={query}"
            )

            print(f"\nEntrando Falabella: {url}")

            # domcontentloaded es mucho más rápido que load
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            # esperar productos
            try:
                page.wait_for_selector(
                    "[data-testid='result-pod']",
                    timeout=20000
                )
            except:
                try:
                    page.wait_for_selector(
                        ".pod-subTitle, .pod-title",
                        timeout=15000
                    )
                except:
                    print("No se encontraron selectores, guardando screenshot...")
                    page.screenshot(path="falabella_debug.png")

            # scroll para activar lazy load
            page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight / 2)"
            )
            page.wait_for_timeout(2000)

            cards = page.query_selector_all(
                "[data-testid='result-pod']"
            )

            if not cards:
                cards = page.query_selector_all(".pod")

            print(f"Tarjetas encontradas: {len(cards)}")

            for card in cards:

                try:

                    nombre_el = (
                        card.query_selector("[data-testid='pod-displaySubTitle']")
                        or card.query_selector(".pod-subTitle")
                        or card.query_selector(".pod-title")
                    )

                    if not nombre_el:
                        continue

                    nombre = nombre_el.inner_text().strip()

                    if len(nombre.split()) < 2:
                        continue

                    precio_el = (
                        card.query_selector("[data-testid='pod-prices-0-price-0']")
                        or card.query_selector(".copy10.primary")
                        or card.query_selector(".prices-0")
                        or card.query_selector("[class*='price']")
                    )

                    if not precio_el:
                        continue

                    precio = clean_price(
                        precio_el.inner_text().strip()
                    )

                    if precio <= 1000:
                        continue

                    img_el = card.query_selector("img")
                    imagen = ""
                    if img_el:
                        imagen = (
                            img_el.get_attribute("src")
                            or img_el.get_attribute("data-src")
                            or ""
                        )

                    link_el = card.query_selector("a")
                    link = url
                    if link_el:
                        href = link_el.get_attribute("href") or ""
                        if href.startswith("http"):
                            link = href
                        elif href.startswith("/"):
                            link = f"https://www.falabella.com.co{href}"

                    productos.append({
                        "product": nombre,
                        "price": precio,
                        "store": "Falabella",
                        "url": link,
                        "image": imagen,
                    })

                    print(f"✅ {nombre} - ${precio}")

                except Exception as e:
                    print(f"Error en tarjeta: {e}")
                    continue

            browser.close()

    except Exception as e:
        print(f"Error Falabella: {e}")

    vistos = set()
    unicos = []

    for p in productos:
        key = (p["product"], p["price"])
        if key in vistos:
            continue
        vistos.add(key)
        unicos.append(p)

    print(f"\nTOTAL FALABELLA: {len(unicos)}")
    return unicos