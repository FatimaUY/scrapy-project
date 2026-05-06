import scrapy


class ProductspiderSpider(scrapy.Spider):
    name = "productspider"
    allowed_domains = ["www.centrale-brico.com"]
    start_urls = ["https://www.centrale-brico.com/electricite/eclairage/spot-encastrable"]

    def parse(self, response):
        pass
