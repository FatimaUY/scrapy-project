# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from webscraper.items import CategorieItem, ProductItem
import re

class WebscraperPipeline:
    def process_item(self, item, spider):
        
        adapter = ItemAdapter(item)

        #Nettoyage
        if adapter.get("name_cat"):
            adapter["name_cat"] = adapter["name_cat"].strip()
            adapter["name_cat"] = adapter["name_cat"].replace(",", " - ")
            adapter["name_cat"] = adapter["name_cat"].replace('"', "")


        if isinstance(item, CategorieItem):
            if not item["url_cat"].startswith("https://"):
                raise DropItem(f"URL invalide: {item['url_cat']}")

        if "price_product" in item:
            item["price_product"] = self._clean_price(item.get("price_product"))

        #Validation
        if isinstance(item, ProductItem):
            return item    
        
        if not item["url_cat"].startswith("https://"):
            raise DropItem(f"URL invalide: {item['url_cat']}")


        return item
    
    @staticmethod
    def _clean_price(raw: str) -> str | None:
        """
        Normalise une chaîne de prix issue de Centrale Brico.

        Formats gérés :
          "24€12"   → "24.12"   (€ = séparateur décimal)
          "24,12 €" → "24.12"   (format français standard)
          "24.12"   → "24.12"   (déjà normalisé)
        """
        if not raw:
            return None
        cleaned = raw.strip()
        # ① "24€12" → le € est le séparateur décimal
        cleaned = cleaned.replace("€", ".")
        # ② Supprime tout sauf chiffres, virgule et point
        cleaned = re.sub(r"[^\d,.]", "", cleaned)
        # ③ Virgule décimale française → point
        cleaned = cleaned.replace(",", ".")
        # ④ Supprime doubles points et point final résiduel
        cleaned = re.sub(r"\.{2,}", ".", cleaned)
        cleaned = cleaned.rstrip(".")
        return cleaned if cleaned else None