import scrapy
from webscraper.items import CategorieItem


class BricoSpiderSpider(scrapy.Spider):
    name = "brico_spider"
    allowed_domains = ["centrale-brico.com"]
    start_urls = ["https://www.centrale-brico.com"]

    def __init__(self):
        self.seen_ids = set()
        self.id_to_url = {} 

    def parse(self, response):
        categories = response.css('ul.menu-home > li.category')
        yield from self.parse_categories(categories, parent=response.url)

    def parse_categories(self, categories, parent):

        for cat in categories:
            link = cat.css('a[id^="category-"]')

            name_cat = link.css('::text').get()
            url_cat = link.css('::attr(href)').get()
            id_cat = link.css('::attr(id)').get()

            if not (name_cat and id_cat):
                continue

            name_cat = name_cat.strip()

            if id_cat in self.seen_ids:
                continue
            self.seen_ids.add(id_cat)

            self.id_to_url[id_cat] = url_cat

            submenu = cat.xpath('./div[contains(@class,"submenu")]//ul/li[@class="category"]')

            is_page = 0 if submenu else 1

            if parent in self.id_to_url:
                parent_url = self.id_to_url[parent]
            else:
                parent_url = parent  

            item = CategorieItem()
            item["name_cat"] = name_cat
            item["url_cat"] = url_cat
            item["id_cat"] = id_cat
            item["is_page"] = is_page
            item["parent_cat"] = parent_url

            yield item

            if submenu:
                yield from self.parse_categories(submenu, parent=id_cat)