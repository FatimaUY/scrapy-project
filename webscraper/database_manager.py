#!/usr/bin/env python3
"""
Gestionnaire de base de données simplifié pour le projet de scraping BricoSimplon
"""

import sqlite3


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
        """Créer les tables catégories et produits avec clé étrangère"""
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
            
            # Table des produits avec clé étrangère vers categories
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id_product TEXT PRIMARY KEY,
                    name_product TEXT NOT NULL,
                    price REAL NOT NULL,
                    url_product TEXT NOT NULL,
                    id_cat TEXT NOT NULL,
                    category_name TEXT NOT NULL,
                    category_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_cat) REFERENCES categories (id_cat)
                )
            ''')
            
            # Index pour optimiser les requêtes
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_categories_parent 
                ON categories(parent_cat)
            ''')
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_products_category 
                ON products(id_cat)
            ''')
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_products_price 
                ON products(price)
            ''')
            
            self.connection.commit()
            print("Tables créées avec succès (avec clé étrangère)")
            return True
            
        except sqlite3.Error as e:
            print(f"Erreur lors de la création des tables: {e}")
            return False
    
    def get_stats(self):
        """Obtenir des statistiques simples sur la base de données"""
        try:
            stats = {}
            
            # Nombre de catégories
            self.cursor.execute("SELECT COUNT(*) FROM categories")
            stats['categories_count'] = self.cursor.fetchone()[0]
            
            # Nombre de produits
            self.cursor.execute("SELECT COUNT(*) FROM products")
            stats['products_count'] = self.cursor.fetchone()[0]
            
            # Nombre de catégories parentes (niveau racine)
            self.cursor.execute("SELECT COUNT(*) FROM categories WHERE parent_cat IS NULL")
            stats['root_categories_count'] = self.cursor.fetchone()[0]
            
            return stats
            
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération des statistiques: {e}")
            return {}


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
        
        # Fermer la connexion
        db_manager.disconnect()


if __name__ == "__main__":
    main()
