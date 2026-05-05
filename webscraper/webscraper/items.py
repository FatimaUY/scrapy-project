# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class CategorieItem(scrapy.Item):
    id_cat = scrapy.Field()
    name_cat = scrapy.Field()
    url_cat = scrapy.Field()
    is_page = scrapy.Field()
    parent_cat = scrapy.Field()