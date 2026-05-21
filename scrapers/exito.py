import requests


def scrape_exito(query, max_pages=1):

    resultados = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json"
    }

    for page in range(max_pages):

        try:

            url = (
                f"https://www.exito.com/api/catalog_system/pub/products/search/"
                f"?ft={query}"
                f"&_from={page * 50}"
                f"&_to={(page * 50) + 49}"
            )

            print(f"\nConsultando API Éxito:")
            print(url)

            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )
            print("Status:", response.status_code)
            if response.status_code not in [200, 206]:

                
                print("Error status:", response.status_code)
                continue

            data = response.json()

            print("Productos encontrados:", len(data))

            for item in data:

                try:

                    name = item.get("productName", "Sin nombre")

                    link = (
                        "https://www.exito.com/"
                        + item.get("linkText", "")
                        + "/p"
                    )

                    image = ""

                    items = item.get("items", [])

                    if items:

                        images = items[0].get("images", [])

                        if images:
                            image = images[0].get("imageUrl", "")

                    price = 0

                    if items:

                        sellers = items[0].get("sellers", [])

                        if sellers:

                            commertial = sellers[0].get(
                                "commertialOffer",
                                {}
                            )

                            price = commertial.get("Price", 0)

                    resultados.append({
                        "store": "Exito",
                        "product": name,
                        "price": price,
                        "image": image,
                        "url": link
                    })

                except Exception as e:
                    print("Error producto:", e)

        except Exception as e:
            print("Error API:", e)

    # eliminar duplicados
    final = []

    seen = set()

    for r in resultados:

        key = (
            r["product"],
            r["image"]
        )

        if key not in seen:
            seen.add(key)
            final.append(r)

    print("TOTAL EXITO:", len(final))

    return final