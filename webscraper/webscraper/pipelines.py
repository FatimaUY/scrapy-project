# useful for handling different item types with a single interface
import sqlite3
import re
import hashlib
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
 
 
class DataCleaningPipeline:
    """Pipeline pour nettoyer les données extraites"""
 
    def process_item(self, item, spider):
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
        """Nettoyer et normaliser les prix"""
        if not price_str:
            return None

        # Supprimer les caractères non numériques sauf . et ,
        cleaned = re.sub(r'[^\d.,]', '', str(price_str))

        # Remplacer la virgule par point pour la conversion
        cleaned = cleaned.replace(',', '.')

        # Extraire le premier nombre trouvé (correction pour virgule)
        match = re.search(r'\d+\.?\d*', cleaned)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None

        return None
 
    def clean_url(self, url):
        """Nettoyer les URLs"""
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
            if not adapter.get('price'):
                raise DropItem("Produit sans prix")
            if not adapter.get('category_name'):
                raise DropItem("Produit sans catégorie")
            if not adapter.get('id_product'):
                # Générer un ID si manquant
                adapter['id_product'] = self.generate_id(adapter['name_product'], adapter['url_product'])
 
        return item
 
    def generate_id(self, name, url):
        """Générer un ID unique à partir du nom et de l'URL"""
        unique_string = f"{name}_{url}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]
 
 
class DuplicateRemovalPipeline:
    """Pipeline pour éliminer les doublons"""
 
    def __init__(self):
        self.seen_categories = set()
        self.seen_products = set()
 
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
 
        # Vérifier les doublons de catégories
        if 'id_cat' in adapter:
            cat_id = adapter['id_cat']
            if cat_id in self.seen_categories:
                spider.logger.info(f"Catégorie en double ignorée: {adapter.get('name_cat', 'Unknown')}")
                raise DropItem(f"Catégorie en double: {cat_id}")
            self.seen_categories.add(cat_id)
 
        # Vérifier les doublons de produits
        if 'id_product' in adapter:
            product_id = adapter['id_product']
            if product_id in self.seen_products:
                spider.logger.info(f"Produit en double ignoré: {adapter.get('name_product', 'Unknown')}")
                raise DropItem(f"Produit en double: {product_id}")
            self.seen_products.add(product_id)
 
        return item
 
 
class DatabasePipeline:
    """Pipeline pour stocker les données dans la base de données SQLite"""
 
    def __init__(self, sqlite_db, sqlite_table_categories, sqlite_table_products):
        self.sqlite_db = sqlite_db
        self.sqlite_table_categories = sqlite_table_categories
        self.sqlite_table_products = sqlite_table_products
 
    @classmethod
    def from_crawler(cls, crawler):
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
        """Initialiser la connexion à la base de données"""
        self.connection = sqlite3.connect(self.sqlite_db)
        self.cursor = self.connection.cursor()
 
        # Créer les tables si elles n'existent pas
        self.create_tables()
 
    def close_spider(self, spider):
        """Fermer la connexion à la base de données"""
        self.connection.close()
 
    def create_tables(self):
        """Créer les tables catégories et produits"""
 
        # Table des catégories
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
 
        # Table des produits avec clé étrangère vers categories
        self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.sqlite_table_products} (
                id_product TEXT PRIMARY KEY,
                name_product TEXT NOT NULL,
                price REAL NOT NULL,
                url_product TEXT NOT NULL,
                id_cat TEXT NOT NULL,
                category_name TEXT NOT NULL,
                category_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_cat) REFERENCES {self.sqlite_table_categories} (id_cat)
            )
        ''')
 
        self.connection.commit()
 
    def process_item(self, item, spider):
        """Stocker l'item dans la base de données"""
        adapter = ItemAdapter(item)
 
        try:
            # Insérer ou mettre à jour une catégorie
            if 'name_cat' in adapter:
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
 
            # Insérer ou mettre à jour un produit
            if 'name_product' in adapter:
                self.cursor.execute(f'''
                    INSERT OR REPLACE INTO {self.sqlite_table_products} 
                    (id_product, name_product, price, url_product, id_cat, category_name, category_url, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    adapter.get('id_product'),
                    adapter.get('name_product'),
                    adapter.get('price'),
                    adapter.get('url_product'),
                    adapter.get('id_cat'),  # Ajout de la clé étrangère
                    adapter.get('category_name'),
                    adapter.get('category_url')
                ))
 
            self.connection.commit()
            spider.logger.info(f"Item stocké dans la base de données: {adapter.get('name_cat', adapter.get('name_product', 'Unknown'))}")
 
        except sqlite3.Error as e:
            spider.logger.error(f"Erreur lors du stockage dans la base de données: {e}")
            raise DropItem(f"Erreur base de données: {e}")
 
        return item
