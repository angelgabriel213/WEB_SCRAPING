# BuyWise PRO — Comparador de precios

Aplicación web desarrollada con Python y Flask para consultar productos en diferentes comercios, recopilar resultados mediante scraping/API, normalizar información y agrupar productos similares para facilitar la comparación de precios.

## Tecnologías

- Python
- Flask
- Requests
- BeautifulSoup / lxml
- Playwright
- RapidFuzz
- Sentence Transformers
- Scikit-learn
- Pandas / OpenPyXL
- HTML / CSS / JavaScript

## Arquitectura

```text
WEB_SCRAPING/
├── app.py
├── scrapers/
│   ├── exito.py
│   ├── olimpica.py
│   ├── falabella.py
│   ├── mercadolibre.py
│   └── alkosto.py
├── utils/
│   ├── ai_compare.py
│   ├── compare.py
│   ├── normalize.py
│   ├── size.py
│   └── export.py
├── templates/
├── static/
└── requirements.txt
```

## Funcionalidades

- Búsqueda de productos desde una interfaz web.
- Consulta de múltiples comercios.
- Integración de APIs y scraping según la fuente.
- Extracción de nombre, precio, imagen y URL.
- Limpieza y deduplicación de resultados.
- Normalización de nombres y tamaños.
- Comparación de productos mediante similitud de texto.
- Agrupación de productos similares de diferentes tiendas.
- Uso de embeddings con Sentence Transformers y similitud coseno para apoyar la identificación de productos relacionados.
- Ordenamiento de resultados por precio.

## Fuentes integradas

El proyecto contiene scrapers para:

- Éxito
- Olímpica
- Falabella
- Mercado Libre
- Alkosto

La disponibilidad y estabilidad de cada fuente puede variar porque las páginas y APIs externas cambian con el tiempo.

## Comparación de productos

El módulo `utils/compare.py` utiliza normalización, extracción de tamaño y RapidFuzz para comparar productos.

El módulo `utils/ai_compare.py` utiliza el modelo `all-MiniLM-L6-v2` de Sentence Transformers y similitud coseno, junto con reglas adicionales para tamaño y palabras comunes.

Esto permite combinar similitud semántica con reglas de validación antes de agrupar productos.

## Instalación

Se recomienda Python 3.11 o una versión compatible con las dependencias.

```bash
git clone https://github.com/angelgabriel213/WEB_SCRAPING.git
cd WEB_SCRAPING

python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Instala las dependencias:

```bash
pip install -r requirements.txt
```

Para los scrapers que utilizan Playwright:

```bash
playwright install chromium
```

## Ejecución

```bash
python app.py
```

La aplicación se inicia en:

```text
http://127.0.0.1:5000
```

## Consideraciones

Los scrapers dependen de estructuras y servicios externos. Un cambio en selectores, endpoints, políticas de acceso o respuestas de una tienda puede requerir actualizar el scraper correspondiente.

El proyecto está orientado a aprendizaje y portafolio de desarrollo de software, automatización, consumo de APIs, procesamiento de datos y técnicas de comparación semántica.

## Próximas mejoras

- Persistencia de resultados y caché para reducir scraping repetitivo.
- Sistema de comparación más preciso entre presentaciones y tamaños.
- Pruebas automatizadas para los scrapers.
- Manejo centralizado de timeouts, reintentos y errores.
- Observabilidad y logs estructurados.
- Despliegue reproducible mediante Docker.
