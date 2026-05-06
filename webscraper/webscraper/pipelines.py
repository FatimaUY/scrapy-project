# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from webscraper.items import CategorieItem, ProductItem

class WebscraperPipeline:
    def process_item(self, item, spider):
        
        adapter = ItemAdapter(item)

        #Nettoyage
        if adapter.get("name_cat"):
            adapter["name_cat"] = adapter["name_cat"].strip()
            adapter["name_cat"] = adapter["name_cat"].replace(",", " - ")
            adapter["name_cat"] = adapter["name_cat"].replace('"', "")

        if adapter.get("url_cat"):
            adapter["url_cat"] = adapter["url_cat"].strip()


        #Validation
        if isinstance(item, ProductItem):
            return item    
        
        if not item["url_cat"].startswith("https://"):
            raise DropItem(f"URL invalide: {item['url_cat']}")


        return item
    
    def process_product(self, item, spider):
        
        adapter = ItemAdapter(item)

        #Nettoyage
        if adapter.get("name_cat"):
            adapter["name_cat"] = adapter["name_cat"].strip()
            adapter["name_cat"] = adapter["name_cat"].replace(",", " - ")
            adapter["name_cat"] = adapter["name_cat"].replace('"', "")

        if adapter.get("url_product"):
            adapter["url_product"] = adapter["url_product"].strip()


        #Validation
        if not item["url_product"].startswith("https://"):
            raise DropItem(f"URL invalide: {item['url_product']}")


        return item