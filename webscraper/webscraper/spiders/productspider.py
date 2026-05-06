import re
import scrapy
from webscraper.items import ProductItem


class ProductSpider(scrapy.Spider):
    name = "productspider"
    allowed_domains = ["www.centrale-brico.com"]
    start_urls = ["https://www.centrale-brico.com/electricite/eclairage/spot-encastrable"]


    custom_settings = {
        "DOWNLOAD_DELAY": 1.5,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1,
        "ROBOTSTXT_OBEY": True,
        "FEEDS": {
            "centrale_brico_spots.csv": {
                "format": "csv",
                "encoding": "utf-8-sig",   
                "overwrite": True,
            },
            "centrale_brico_spots.json": {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True,
                "indent": 2,
            },
        },
        "LOG_LEVEL": "INFO",
    }


    def parse(self, response):
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
        ) or "Spot encastrable"

        products = response.css("article.product-miniature, li.ajax_block_product")

        if not products:
            products = response.css(".product-container, .product_list .item")

        for product in products:
            yield from self._parse_product_card(product, category, response)

        next_page = response.css(
            "a[rel='next']::attr(href), "
            ".pagination a.next::attr(href), "
            "ul.pagination li:last-child a::attr(href)"
        ).get()

        if next_page:
            yield response.follow(next_page, callback=self.parse)


    def _parse_product_card(self, card, category, response):
       
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

        price = price_text.strip() if price_text else None

        yield ProductItem(
            id_product    = product_id,
            name_product  = (product_name or "").strip(),
            price_product = price,
            url_product   = product_url,
            cat_product   = category,
        )

