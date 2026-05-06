#!/usr/bin/env python3
"""
Gestionnaire de base de données pour le projet de scraping BricoSimplon
Ce script permet de créer, gérer et interroger la base de données SQLite
"""

import sqlite3
import os
from datetime import datetime


class DatabaseManager:
    """Classe pour gérer la base de données SQLite"""
    
    def __init__(self, db_path='scraping_data.db'):
        self.db_path = db_path
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Établir la connexion à la base de données"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            print(f"Connexion établie avec la base de données: {self.db_path}")
            return True
        except sqlite3.Error as e:
            print(f"Erreur de connexion à la base de données: {e}")
            return False
    
    def disconnect(self):
        """Fermer la connexion à la base de données"""
        if self.connection:
            self.connection.close()
            print("Connexion à la base de données fermée")
    
    def create_tables(self):
        """Créer les tables catégories et produits"""
        try:
            # Table des catégories
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id_cat TEXT PRIMARY KEY,
                    name_cat TEXT NOT NULL,
                    url_cat TEXT NOT NULL,
                    parent_cat TEXT,
                    is_page INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table des produits
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id_product TEXT PRIMARY KEY,
                    name_product TEXT NOT NULL,
                    price REAL NOT NULL,
                    url_product TEXT NOT NULL,
                    category_name TEXT NOT NULL,
                    category_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Créer des index pour optimiser les requêtes
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_categories_parent 
                ON categories(parent_cat)
            ''')
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_products_category 
                ON products(category_name)
            ''')
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_products_price 
                ON products(price)
            ''')
            
            self.connection.commit()
            print("Tables créées avec succès")
            return True
            
        except sqlite3.Error as e:
            print(f"Erreur lors de la création des tables: {e}")
            return False
    
    def get_stats(self):
        """Obtenir des statistiques sur la base de données"""
        try:
            stats = {}
            
            # Nombre de catégories
            self.cursor.execute("SELECT COUNT(*) FROM categories")
            stats['categories_count'] = self.cursor.fetchone()[0]
            
            # Nombre de produits
            self.cursor.execute("SELECT COUNT(*) FROM products")
            stats['products_count'] = self.cursor.fetchone()[0]
            
            # Prix moyen des produits
            self.cursor.execute("SELECT AVG(price) FROM products")
            avg_price = self.cursor.fetchone()[0]
            stats['average_price'] = round(avg_price, 2) if avg_price else 0
            
            # Prix minimum et maximum
            self.cursor.execute("SELECT MIN(price), MAX(price) FROM products")
            min_price, max_price = self.cursor.fetchone()
            stats['min_price'] = min_price if min_price else 0
            stats['max_price'] = max_price if max_price else 0
            
            # Nombre de catégories parentes (niveau racine)
            self.cursor.execute("SELECT COUNT(*) FROM categories WHERE parent_cat IS NULL")
            stats['root_categories_count'] = self.cursor.fetchone()[0]
            
            return stats
            
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération des statistiques: {e}")
            return {}
    
    def export_to_csv(self, output_dir='exports'):
        """Exporter les données vers des fichiers CSV"""
        try:
            import csv
            
            # Créer le répertoire d'export s'il n'existe pas
            os.makedirs(output_dir, exist_ok=True)
            
            # Exporter les catégories
            with open(f'{output_dir}/categories_export.csv', 'w', newline='', encoding='utf-8') as csvfile:
                cursor = self.connection.cursor()
                cursor.execute("SELECT * FROM categories")
                
                writer = csv.writer(csvfile)
                writer.writerow([description[0] for description in cursor.description])  # En-têtes
                writer.writerows(cursor.fetchall())
            
            # Exporter les produits
            with open(f'{output_dir}/products_export.csv', 'w', newline='', encoding='utf-8') as csvfile:
                cursor = self.connection.cursor()
                cursor.execute("SELECT * FROM products")
                
                writer = csv.writer(csvfile)
                writer.writerow([description[0] for description in cursor.description])  # En-têtes
                writer.writerows(cursor.fetchall())
            
            print(f"Données exportées dans le répertoire: {output_dir}")
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'export CSV: {e}")
            return False
    
    def search_products(self, keyword=None, min_price=None, max_price=None, category=None):
        """Rechercher des produits avec des filtres"""
        try:
            query = "SELECT * FROM products WHERE 1=1"
            params = []
            
            if keyword:
                query += " AND name_product LIKE ?"
                params.append(f"%{keyword}%")
            
            if min_price:
                query += " AND price >= ?"
                params.append(min_price)
            
            if max_price:
                query += " AND price <= ?"
                params.append(max_price)
            
            if category:
                query += " AND category_name LIKE ?"
                params.append(f"%{category}%")
            
            query += " ORDER BY price ASC"
            
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
            
        except sqlite3.Error as e:
            print(f"Erreur lors de la recherche: {e}")
            return []
    
    def get_categories_hierarchy(self):
        """Obtenir la hiérarchie des catégories"""
        try:
            self.cursor.execute('''
                SELECT c1.id_cat, c1.name_cat, c1.url_cat, c1.parent_cat, c1.is_page,
                       c2.name_cat as parent_name
                FROM categories c1
                LEFT JOIN categories c2 ON c1.parent_cat = c2.name_cat
                ORDER BY c1.parent_cat, c1.name_cat
            ''')
            
            return self.cursor.fetchall()
            
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération de la hiérarchie: {e}")
            return []


def main():
    """Fonction principale pour tester le gestionnaire de base de données"""
    print("=== Gestionnaire de base de données BricoSimplon ===")
    
    # Créer une instance du gestionnaire
    db_manager = DatabaseManager()
    
    # Se connecter
    if db_manager.connect():
        # Créer les tables
        db_manager.create_tables()
        
        # Afficher les statistiques
        stats = db_manager.get_stats()
        print("\n=== Statistiques de la base de données ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        # Afficher la hiérarchie des catégories
        print("\n=== Hiérarchie des catégories ===")
        categories = db_manager.get_categories_hierarchy()
        for cat in categories[:10]:  # Limiter à 10 pour l'affichage
            print(f"ID: {cat[0]}, Nom: {cat[1]}, Parent: {cat[3]}")
        
        # Exporter les données
        db_manager.export_to_csv()
        
        # Fermer la connexion
        db_manager.disconnect()


if __name__ == "__main__":
    main()
