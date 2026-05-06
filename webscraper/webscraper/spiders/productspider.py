import json
import re
import scrapy
from webscraper.items import ProductItem


class ProductSpider(scrapy.Spider):
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
        import glob

        files = sorted(glob.glob("output/categories_2026-05-06.json"))
        if not files:
            self.logger.error("Aucun fichier categories.json trouvé dans output/")
            return

        cat_file = files[-1]
        self.logger.info(f"Lecture des catégories depuis : {cat_file}")

        with open(cat_file, encoding="utf-8") as f:
            categories = json.load(f)

        count = 0
        for cat in categories:
            if cat.get("is_page") == 1 and cat.get("url_cat"):
                if count >= 3:
                    break

                self.logger.info(f"[CAT {count+1}] {cat['name_cat']} → {cat['url_cat']}")

                yield scrapy.Request(
                    url=cat["url_cat"],
                    callback=self.parse,
                    cb_kwargs={
                        "category": cat["name_cat"],
                        "id_cat": cat["id_cat"],
                    },
                )
                count += 1

    def parse(self, response, category="", id_cat=None):
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