import requests


def scrape_olimpica(query):

    resultados = []

    url = (
        "https://www.olimpica.com/"
        "api/catalog_system/pub/products/search/"
        f"?ft={query}"
    )

    print("\nConsultando API Olímpica:")
    print(url)

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        print(
            "Status Olímpica:",
            response.status_code
        )

        if response.status_code not in [200, 206]:

            return []

        data = response.json()

        print(
            "Productos Olímpica:",
            len(data)
        )

        for item in data:

            try:

                name = item.get(
                    "productName",
                    "Sin nombre"
                )

                link = item.get(
                    "link",
                    ""
                )

                items = item.get(
                    "items",
                    []
                )

                if not items:
                    continue

                seller = (
                    items[0]
                    .get("sellers", [{}])[0]
                )

                offer = seller.get(
                    "commertialOffer",
                    {}
                )

                price = (
                    offer.get("Price")
                    or 0
                )

                if price <= 0:
                    continue

                images = items[0].get(
                    "images",
                    []
                )

                image = ""

                if images:

                    image = images[0].get(
                        "imageUrl",
                        ""
                    )

                # construir URL limpia
                if not link:
                    product_url = (
                        "https://www.olimpica.com"
                    )

                elif "olimpica.com" in link:
                    product_url = (
                        link
                        .replace("https//", "https://")
                        .replace("http//", "http://")
                    )

                else:
                    product_url = (
                        "https://www.olimpica.com"
                        + link
                    )

                resultados.append({

                    "store": "Olimpica",

                    "product": name,

                    "price": float(price),

                    "image": image,

                    "url": product_url
                })

                print(
                    f"✅ {name} - ${price}"
                )

            except Exception as e:

                print(
                    "Error producto:",
                    e
                )

    except Exception as e:

        print(
            "Error Olímpica:",
            e
        )

    print(
        "\nTOTAL OLIMPICA:",
        len(resultados)
    )

    return resultados