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
    
class ProductItem(scrapy.Item):
    id_product = scrapy.Field()
    name_product = scrapy.Field()
    price_product = scrapy.Field()
    url_product = scrapy.Field()
    cat_product = scrapy.Field()    
    id_cat = scrapy.Field() 