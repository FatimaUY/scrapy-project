
"""
Pipeline module to process Scrapy items.

Defines the processing chain applied to each 
extracted item: data cleaning, validation, duplicate removal, and
persistence in a SQLite database.
"""

import sqlite3
import re
import hashlib
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from webscraper.items import CategorieItem, ProductItem

 
 
class DataCleaningPipeline:
    """Pipeline to clean extracted data"""
 
    def process_item(self, item, spider):
        """        
        Clean text fields, prices, and URLs.
        
        :param item: The Scrapy item to clean.
        :param spider: The spider that produced the item.
        :return: The cleaned item.
        """

        adapter = ItemAdapter(item)
 
        # Nettoyage des champs de texte
        for field_name, value in adapter.items():
            if isinstance(value, str):
                # Supprimer les espaces inutiles
                cleaned_value = value.strip()
                # Nettoyer les caractères spéciaux multiples
                cleaned_value = re.sub(r'\s+', ' ', cleaned_value)
                # Nettoyer les sauts de ligne
                cleaned_value = re.sub(r'\n+', ' ', cleaned_value)
                adapter[field_name] = cleaned_value
 
        # Nettoyage spécifique pour les prix
        if 'price' in adapter and adapter['price']:
            adapter['price'] = self.clean_price(adapter['price'])
 
        # Nettoyage des URLs
        if 'url_cat' in adapter and adapter['url_cat']:
            adapter['url_cat'] = self.clean_url(adapter['url_cat'])
 
        if 'url_product' in adapter and adapter['url_product']:
            adapter['url_product'] = self.clean_url(adapter['url_product'])
 
        return item
 
    def clean_price(self, price_str):
        """
        Clean and normalize a price string in the Centrale Brico format.
        Handles the following formats:
        - ``"49€27"`` → ``49.27``  (the € symbol replaces the decimal separator)
        - ``"24,12 €"`` → ``24.12`` (French decimal format)
        - ``"24.12"``  → ``24.12`` (already normalized)
        
        :param price_str: The raw string representing the price.
        :return: The price as a float, or ``None`` if conversion fails.
        :rtype: float | None
        """

        if not price_str:
            return None

        cleaned = str(price_str).strip()

        if re.search(r'\d€\d', cleaned):
            cleaned = re.sub(r'(\d)€(\d)', r'\1.\2', cleaned)  
            cleaned = re.sub(r'[^\d.]', '', cleaned)

        elif ',' in cleaned:
            cleaned = re.sub(r'[^\d.,]', '', cleaned)
            cleaned = cleaned.replace('.', '')           
            cleaned = cleaned.replace(',', '.')          

        else:
            cleaned = re.sub(r'[^\d.]', '', cleaned)
            if re.fullmatch(r'\d{1,3}(\.\d{3})+', cleaned):
                cleaned = cleaned.replace('.', '')       

        try:
            return float(cleaned)
        except ValueError:
            return None
 
    def clean_url(self, url):
        """
        Clean URLs by removing unnecessary tracking parameters and anchor fragments.
        
        :param url: The raw URL to clean.
        :return: The cleaned URL, or ``None`` if the URL is empty.
        :rtype: str | None
        """

        if not url:
            return None
 
        # Supprimer les paramètres de tracking inutiles
        url = re.sub(r'[?&](utm_[^&]*|ref=[^&]*)', '', url)
        # Supprimer les fragments d'ancre
        url = re.sub(r'#.*$', '', url)
 
        return url.strip()
 
 
class DataValidationPipeline:
    """Pipeline pour valider les données"""
 
    def process_item(self, item, spider):
        """
        Validates required fields for category and product items. Raises a
        :class:`~scrapy.exceptions.DropItem` if a required field is missing. 
        Generates a truncated MD5 identifier if the ``id_cat`` or ``id_product`` field is missing.
        
        :param item: The Scrapy item to validate.
        :param spider: The spider that produced the item.
        :return: The validated item.
        :raises DropItem: If a required field is missing.
        """

        adapter = ItemAdapter(item)
 
        # Validation pour les catégories
        if 'name_cat' in adapter:
            if not adapter.get('name_cat'):
                raise DropItem("Catégorie sans nom")
            if not adapter.get('url_cat'):
                raise DropItem("Catégorie sans URL")
            if not adapter.get('id_cat'):
                # Générer un ID si manquant
                adapter['id_cat'] = self.generate_id(adapter['name_cat'], adapter['url_cat'])
 
        # Validation pour les produits
        if 'name_product' in adapter:
            if not adapter.get('name_product'):
                raise DropItem("Produit sans nom")
            if not adapter.get('url_product'):
                raise DropItem("Produit sans URL")
            if not adapter.get('id_product'):
                # Générer un ID si manquant
                adapter['id_product'] = self.generate_id(adapter['name_product'], adapter['url_product'])
 
        return item
 
    def generate_id(self, name, url):
        """
        Generates a unique 16-character identifier based on the name and URL.
        
        :param name: The name of the entity (category or product).
        :param url: The URL of the entity.
        :return: A 16-character hexadecimal identifier.
        :rtype: str
        """
        unique_string = f"{name}_{url}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]
 
 
class DuplicateRemovalPipeline:
    """Pipeline to remove duplicate categories and products based on their identifiers"""
 
    def __init__(self):
        self.seen_categories = set()
        self.seen_products = set()
 
    def process_item(self, item, spider):
        """
        Rejects the item if its identifier has already been processed.
        
        :param item: The Scrapy item to check.
        :param spider: The spider that produced the item.
        :return: The item if it is unique.
        :raises DropItem: If the item is a duplicate.
        """

        adapter = ItemAdapter(item)
 
        # Vérifier les doublons de catégories
        if isinstance(item, CategorieItem):
            cat_id = adapter['id_cat']
            if cat_id in self.seen_categories:
                spider.logger.info(f"Catégorie en double ignorée ")
                raise DropItem(f"Catégorie en double: {cat_id}")
            self.seen_categories.add(cat_id)
        
        # Vérifier les doublons de produits
        elif isinstance(item, ProductItem):
            product_id = adapter['id_product']
            if product_id in self.seen_products:
                spider.logger.info(f"Produit en double ignoré ")
                raise DropItem(f"Produit en double: {product_id}")
            self.seen_products.add(product_id)
 
        return item
 
class DatabasePipeline:
    """Pipeline to store data in the SQLite database"""

    def __init__(self, sqlite_db, sqlite_table_categories, sqlite_table_products):
        """
        Initializes the pipeline with the database connection parameters.
 
        :param sqlite_db: Path to the SQLite database file.
        :param sqlite_table_categories: Name of the categories table.
        :param sqlite_table_products: Name of the products table.
        """

        self.sqlite_db = sqlite_db
        self.sqlite_table_categories = sqlite_table_categories
        self.sqlite_table_products = sqlite_table_products

    @classmethod
    def from_crawler(cls, crawler):
        """
        Instance the pipeline from Scrapy settings.
        
        Reads the ``DATABASE`` dictionary from settings and uses default values if it's missing.
        
        :param crawler: The current :class:`~scrapy.crawler.Crawler` instance.
        :return: A configured instance of :class:`DatabasePipeline`.
        """

        db_settings = crawler.settings.getdict("DATABASE")
        if not db_settings:
            db_settings = {
                'db': 'scraping_data.db',
                'categories_table': 'categories',
                'products_table': 'products'
            }
        return cls(
            sqlite_db=db_settings['db'],
            sqlite_table_categories=db_settings['categories_table'],
            sqlite_table_products=db_settings['products_table']
        )

    def open_spider(self, spider):
        """
        Open the SQLite connection and create tables if they do not exist.
        
        :param spider: The spider being opened.
        """

        self.connection = sqlite3.connect(self.sqlite_db)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def close_spider(self, spider):
        """
        Close the SQLite connection properly.
 
        :param spider: The spider being closed.
        """

        self.connection.close()

    def create_tables(self):
        """
        Creates the ``categories`` and ``products`` tables in the database if they are missing.
 
        The ``products`` table references the ``categories`` table via a foreign key on ``id_cat``.
        """

        self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.sqlite_table_categories} (
                id_cat TEXT PRIMARY KEY,
                name_cat TEXT NOT NULL,
                url_cat TEXT NOT NULL,
                parent_cat TEXT,
                is_page INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.sqlite_table_products} (
                id_product TEXT PRIMARY KEY,
                name_product TEXT NOT NULL,
                price REAL,
                url_product TEXT NOT NULL,
                id_cat TEXT NOT NULL,
                category_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_cat) REFERENCES {self.sqlite_table_categories} (id_cat)
            )
        ''')

        self.connection.commit()

    def process_item(self, item, spider):
        """
        Inserts or updates a category or product item in the database.
 
        Uses an ``INSERT OR REPLACE`` clause to handle idempotence.
 
        :param item: The Scrapy item to persist.
        :param spider: The spider that produced the item.
        :return: The item unchanged after persistence.
        :raises DropItem: In case of SQLite error.
        """

        adapter = ItemAdapter(item)
        spider.logger.info(f"ITEM RECU: {dict(adapter)}")

        try:
            if adapter.get('name_cat') is not None:
                self.cursor.execute(f'''
                    INSERT OR REPLACE INTO {self.sqlite_table_categories}
                    (id_cat, name_cat, url_cat, parent_cat, is_page, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    adapter.get('id_cat'),
                    adapter.get('name_cat'),
                    adapter.get('url_cat'),
                    adapter.get('parent_cat'),
                    adapter.get('is_page', 0)
                ))

            if adapter.get('name_product') is not None:
                self.cursor.execute(f'''
                    INSERT OR REPLACE INTO {self.sqlite_table_products}
                    (id_product, name_product, price, url_product, id_cat, category_name, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    adapter.get('id_product'),
                    adapter.get('name_product'),
                    adapter.get('price'),
                    adapter.get('url_product'),
                    adapter.get('id_cat'),
                    adapter.get('category_name'),
                ))

            self.connection.commit()
            spider.logger.info("COMMIT OK")

        except sqlite3.Error as e:
            spider.logger.error(f"DB ERROR: {e}")
            raise DropItem(str(e))

        return item