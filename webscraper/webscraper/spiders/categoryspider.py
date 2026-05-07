"""
Module of the category spider for Centrale Brico scraping.

Crawls the main navigation menu of ``www.centrale-brico.com`` 
and produces :class:`~webscraper.items.CategorieItem` 
for each detected category and subcategory, while preserving the parent-child hierarchy.
"""
import scrapy
from webscraper.items import CategorieItem
import datetime


class BricoSpiderSpider(scrapy.Spider):
    """
    Extraction spider for the category hierarchy of ``centrale-brico.com``.
    
    Recursively parses the main menu to build a category tree.
    Each category is exported in CSV and JSON format in the ``output/`` directory,
    with a timestamped filename based on the execution date.
    The ``is_page`` attribute is set to ``1`` for leaf categories (without sub-menu)
    and ``0`` for intermediate nodes.
    """

    
    name = "categoryspider"
    allowed_domains = ["centrale-brico.com"]
    start_urls = ["https://www.centrale-brico.com"]

    today = datetime.date.today()


    custom_settings = {
        "FEEDS": {
            f"output/categories_{today}.csv": {
                "format": "csv",
                "encoding": "utf-8",
                "overwrite": True,
            },
            f"output/categories_{today}.json": {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True,
                "indent": 2,
            },
        }
    }

    def __init__(self):
        """
        Initialize the spider with tracking structures for seen categories.
        
        ``seen_ids`` prevents processing the same category node twice.
        ``id_to_url`` allows retrieving the URL of a parent category from its HTML identifier.
        """
        self.seen_ids = set()
        self.id_to_url = {} 

    def parse(self, response):
        """
        Analyzes the homepage and starts recursion on the main menu categories.
        
        :param response: The HTTP response of the homepage.
        :return: A generator of :class:`~webscraper.items.CategorieItem`.
        """

        categories = response.css('ul.menu-home > li.category')
        yield from self.parse_categories(categories, parent=response.url)

    def parse_categories(self, categories, parent):
        """    
        Browses recursively a list of HTML category elements and produces the corresponding items.
        
        For each category:
        
        - If it has a sub-menu, ``is_page`` is set to ``0`` and the method calls itself
          recursively on the sub-categories, passing the current identifier as parent.
        - If it is a leaf (no sub-menu), ``is_page`` is set to ``1``.
        
        Categories whose identifier has already been processed (present in ``seen_ids``)
        are ignored to avoid duplicates.
        
        :param categories: Scrapy selector on the ``<li class="category">`` elements to process.
        :param parent: Identifier or URL of the parent category, used to fill the ``parent_cat`` field.
        :return: A generator of :class:`~webscraper.items.CategorieItem`.
        """

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