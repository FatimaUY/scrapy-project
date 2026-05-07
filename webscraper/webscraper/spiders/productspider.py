"""
Module du spider de scraping des produits Centrale Brico.
 
Lit les catégories feuilles directement depuis la base de données SQLite
``scraping_data.db`` (table ``categories``), parcourt les pages produits
associées et produit des :class:`~webscraper.items.ProductItem` pour chaque
produit trouvé.
"""
import re
import sqlite3
import scrapy
from webscraper.items import ProductItem


class ProductSpider(scrapy.Spider):
    """
    Spider d'extraction des produits du catalogue ``www.centrale-brico.com``.
 
    Charge les catégories feuilles (``is_page = 1``) depuis la base de données
    SQLite, puis itère sur les pages de listing pour extraire le nom, le prix,
    l'URL et la catégorie de chaque produit. La pagination est gérée
    automatiquement via le lien ``rel="next"``.
    """

    name = "productspider"
    allowed_domains = ["www.centrale-brico.com"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1.5,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1,
        "ROBOTSTXT_OBEY": True,
        "FEEDS": {
            "output/centrale_brico_products.csv": {
                "format": "csv",
                "encoding": "utf-8-sig",
                "overwrite": True,
            },
            "output/centrale_brico_products.json": {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True,
                "indent": 2,
            },
        },
        "LOG_LEVEL": "INFO",
    }

    async def start(self):
        """
        Point d'entrée asynchrone du spider.
 
        Ouvre une connexion SQLite sur ``scraping_data.db``, récupère toutes les
        catégories feuilles (``is_page = 1``), puis génère une
        :class:`~scrapy.http.Request` pour chacune d'elles.
 
        :raises StopIteration: Si aucune catégorie n'est trouvée en base, le spider
            journalise une erreur et s'arrête sans émettre de requête.
        """

        db_path = "scraping_data.db"
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        cursor.execute("SELECT id_cat, name_cat, url_cat FROM categories WHERE is_page = 1")
        categories = cursor.fetchall()
        connection.close()

        if not categories:
            self.logger.error("Aucune catégorie trouvée dans la base de données")
            return

        for count, (id_cat, name_cat, url_cat) in enumerate(categories):
            self.logger.info(f"[CAT {count+1}] {name_cat} → {url_cat}")
            yield scrapy.Request(
                url=url_cat,
                callback=self.parse,
                cb_kwargs={"category": name_cat, "id_cat": id_cat},
            )

    def parse(self, response, category="", id_cat=None):
        """
        Analyse une page de listing produits et suit la pagination.
 
        Si ``category`` n'est pas fourni, tente de le reconstruire depuis le fil
        d'Ariane ou le titre ``<h1>`` de la page. Délègue l'extraction de chaque
        carte produit à :meth:`_parse_product_card`.
 
        :param response: La réponse HTTP de la page de listing.
        :param category: Nom de la catégorie courante (transmis via ``cb_kwargs``).
        :param id_cat: Identifiant de la catégorie courante (transmis via ``cb_kwargs``).
        :return: Un générateur de :class:`~webscraper.items.ProductItem` et de
            :class:`~scrapy.http.Request` pour les pages suivantes.
        """

        if not category:
            breadcrumb_parts = response.css(
                "nav.breadcrumb ol li span[itemprop='name']::text, "
                "nav ol.breadcrumb li a::text, "
                ".breadcrumb li::text, "
                "[itemprop='breadcrumb'] span::text"
            ).getall()

            if not breadcrumb_parts:
                breadcrumb_parts = response.css("h1::text").getall()

            category = " > ".join(
                part.strip() for part in breadcrumb_parts if part.strip()
            ) or "Inconnu"

        products = response.css(
            "article.product-miniature, li.ajax_block_product, "
            ".product-container, .product_list .item"
        )

        for product in products:
            yield from self._parse_product_card(product, category, id_cat, response)

        next_page = response.css(
            "a[rel='next']::attr(href), "
            ".pagination a.next::attr(href), "
            "ul.pagination li:last-child a::attr(href)"
        ).get()

        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse,
                cb_kwargs={"category": category, "id_cat": id_cat},
            )

    def _parse_product_card(self, card, category, id_cat, response):
        """
        Extrait les informations d'un produit depuis sa carte HTML.
 
        L'identifiant produit est recherché en priorité dans le suffixe de l'URL
        (format ``-B\\d+``), puis dans les attributs ``data-id-product`` ou ``id``
        de l'élément HTML.
 
        :param card: Le sélecteur Scrapy pointant sur la carte produit.
        :param category: Nom de la catégorie parente du produit.
        :param id_cat: Identifiant de la catégorie parente.
        :param response: La réponse HTTP de la page de listing (utilisée pour
            résoudre les URLs relatives).
        :return: Un générateur produisant zéro ou un :class:`~webscraper.items.ProductItem`.
        """
        link = card.css("h2.product-title a, h3.product-title a, h2 a, h3 a")
        product_url = link.css("::attr(href)").get()
        product_name = (
            link.css("::attr(title)").get()
            or link.css("::text").get()
            or card.css("[itemprop='name']::text").get()
        )

        if not product_url:
            return

        product_url = response.urljoin(product_url)

        match = re.search(r"-([bB]\d+)$", product_url.rstrip("/"))
        product_id = match.group(1).upper() if match else None

        if not product_id:
            product_id = (
                card.css("::attr(data-id-product)").get()
                or card.attrib.get("data-id-product")
                or card.attrib.get("id", "").replace("product_", "")
            )

        price_node = card.css(".product-price-and-shipping > span")
        price_text = "".join(price_node.css("::text").getall()).strip() if price_node else None

        yield ProductItem(
            id_product    = product_id,
            name_product  = (product_name or "").strip(),
            price         = price_text or None,
            url_product   = product_url,
            category_name = category,
            id_cat        = id_cat,
        )