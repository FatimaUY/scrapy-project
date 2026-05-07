
"""
Module de pipelines de traitement des items Scrapy.
 
Définit la chaîne de traitement appliquée à chaque item extrait :
nettoyage des données, validation, suppression des doublons et
persistance dans une base de données SQLite.
"""

import sqlite3
import re
import hashlib
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from webscraper.items import CategorieItem, ProductItem

 
 
class DataCleaningPipeline:
    """Pipeline pour nettoyer les données extraites"""
 
    def process_item(self, item, spider):
        """
        Nettoie les champs textuels, les prix et les URLs de l'item.

        :param item: L'item Scrapy à nettoyer.
        :param spider: Le spider ayant produit l'item.
        :return: L'item nettoyé.
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
        Nettoie et normalise une chaîne de prix au format Centrale Brico.

        Gère les formats suivants :
        - ``"49€27"`` → ``49.27``  (le symbole € remplace le séparateur décimal)
        - ``"24,12 €"`` → ``24.12`` (format décimal français)
        - ``"24.12"``  → ``24.12`` (déjà normalisé)

        :param price_str: La chaîne brute représentant le prix.
        :return: Le prix en tant que flottant, ou ``None`` si la conversion échoue.
        :rtype: float | None
        """

        if not price_str:
            return None

        # Nettoyage pour le format Centrale Brico
        cleaned = str(price_str).strip()
        
        # Format "49€27" → "49.27"
        cleaned = cleaned.replace("€", ".")
        
        # Supprime tout sauf chiffres, virgule et point
        cleaned = re.sub(r"[^\d,.]", "", cleaned)
        
        # Virgule décimale française → point
        cleaned = cleaned.replace(",", ".")
        
        # Supprime doubles points et point final résiduel
        cleaned = re.sub(r"\.{2,}", ".", cleaned)
        cleaned = cleaned.rstrip(".")
        
        if cleaned:
            try:
                return float(cleaned)
            except ValueError:
                return None
        
        return None
 
    def clean_url(self, url):
        """
        Nettoie une URL en supprimant les paramètres de tracking et les ancres.
 
        :param url: L'URL brute à nettoyer.
        :return: L'URL nettoyée, ou ``None`` si l'URL est vide.
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
        Valide les champs obligatoires d'un item catégorie ou produit.
 
        Lève une :class:`~scrapy.exceptions.DropItem` si un champ requis est absent.
        Génère un identifiant MD5 tronqué si le champ ``id_cat`` ou ``id_product``
        est manquant.
 
        :param item: L'item Scrapy à valider.
        :param spider: Le spider ayant produit l'item.
        :return: L'item validé.
        :raises DropItem: Si un champ obligatoire est absent.
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
        Génère un identifiant unique de 16 caractères à partir du nom et de l'URL.
 
        :param name: Le nom de l'entité (catégorie ou produit).
        :param url: L'URL de l'entité.
        :return: Un identifiant hexadécimal de 16 caractères.
        :rtype: str
        """
        unique_string = f"{name}_{url}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]
 
 
class DuplicateRemovalPipeline:
    """Pipeline pour éliminer les doublons"""
 
    def __init__(self):
        self.seen_categories = set()
        self.seen_products = set()
 
    def process_item(self, item, spider):
        """
        Rejette l'item si son identifiant a déjà été traité.
 
        :param item: L'item Scrapy à vérifier.
        :param spider: Le spider ayant produit l'item.
        :return: L'item si celui-ci est unique.
        :raises DropItem: Si l'item est un doublon.
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
    """Pipeline pour stocker les données dans la base de données SQLite"""

    def __init__(self, sqlite_db, sqlite_table_categories, sqlite_table_products):
        """
        Initialise le pipeline avec les paramètres de connexion à la base de données.
 
        :param sqlite_db: Chemin vers le fichier de base de données SQLite.
        :param sqlite_table_categories: Nom de la table des catégories.
        :param sqlite_table_products: Nom de la table des produits.
        """

        self.sqlite_db = sqlite_db
        self.sqlite_table_categories = sqlite_table_categories
        self.sqlite_table_products = sqlite_table_products

    @classmethod
    def from_crawler(cls, crawler):
        """
        Instancie le pipeline à partir de la configuration Scrapy.
 
        Lit le dictionnaire ``DATABASE`` dans les settings et utilise des valeurs
        par défaut si celui-ci est absent.
 
        :param crawler: L'instance :class:`~scrapy.crawler.Crawler` courante.
        :return: Une instance configurée de :class:`DatabasePipeline`.
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
        Ouvre la connexion SQLite et crée les tables si elles n'existent pas.
 
        :param spider: Le spider en cours d'ouverture.
        """

        self.connection = sqlite3.connect(self.sqlite_db)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def close_spider(self, spider):
        """
        Ferme proprement la connexion à la base de données.
 
        :param spider: Le spider en cours de fermeture.
        """

        self.connection.close()

    def create_tables(self):
        """
        Crée les tables ``categories`` et ``products`` dans la base de données si elles sont absentes.
 
        La table ``products`` référence la table ``categories`` via une clé étrangère sur ``id_cat``.
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
        Insère ou met à jour un item catégorie ou produit dans la base de données.
 
        Utilise une clause ``INSERT OR REPLACE`` pour gérer l'idempotence.
 
        :param item: L'item Scrapy à persister.
        :param spider: Le spider ayant produit l'item.
        :return: L'item inchangé après persistance.
        :raises DropItem: En cas d'erreur SQLite.
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