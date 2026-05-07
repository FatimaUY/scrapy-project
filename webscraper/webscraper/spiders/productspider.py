"""
Module for the product spider of Centrale Brico scraping.
Reads leaf categories directly from the SQLite database ``scraping_data.db``
(table ``categories``), crawls the associated product pages and produces 
:class:`~webscraper.items.ProductItem` for each product found.
"""
import re
import sqlite3
import scrapy
from webscraper.items import ProductItem


class ProductSpider(scrapy.Spider):
    """
    Exctraction spider for the product catalog of ``www.centrale-brico.com``.
    
    Loads leaf categories (``is_page = 1``) from the SQLite database, 
    then iterates over listing pages to extract the name, price, URL and category of each product. 
    Pagination is automatically handled via the ``rel="next"`` link.
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
        Entry point for the spider.
        Opens a SQLite connection to ``scraping_data.db``, retrieves all leaf categories
        (``is_page = 1``), then generates a :class:`~scrapy.http.Request` for each one.
        
        :raises StopIteration: If no category is found in the database, the spider
            logs an error and stops without emitting any request.
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
        Analyzes a product listing page and follows pagination.
        If ``category`` is not provided, attempts to reconstruct it from the breadcrumb
        or the page's ``<h1>`` title. Delegates the extraction of each product card to :meth:`_parse_product_card`.
        
        :param response: The HTTP response of the listing page.
        :param category: Name of the current category (passed via ``cb_kwargs``).
        :param id_cat: Identifier of the current category (passed via ``cb_kwargs``).
        :return: A generator of :class:`~webscraper.items.ProductItem` and
            :class:`~scrapy.http.Request` for the next pages.
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
        Extracts product information from its HTML card.
        The product identifier is primarily searched in the URL suffix (format ``-B\\d+``),
        then in the ``data-id-product`` or ``id`` attributes of the HTML element.
        
        :param card: The Scrapy selector pointing to the product card.
        :param category: Name of the parent category of the product.
        :param id_cat: Identifier of the parent category.
        :param response: The HTTP response of the listing page (used to resolve relative URLs).
        :return: A generator yielding zero or one :class:`~webscraper.items.ProductItem`.
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