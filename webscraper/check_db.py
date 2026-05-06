#!/usr/bin/env python3
"""
Vérification directe de la base de données
"""

import sqlite3

def check_database():
    """Vérifier ce qui est sauvegardé dans la base de données"""
    print("=== VÉRIFICATION DIRECTE DE LA BASE DE DONNÉES ===")
    
    try:
        conn = sqlite3.connect('simple_test.db')
        cursor = conn.cursor()
        
        # 1. Lister les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 Tables dans la base: {[t[0] for t in tables]}")
        
        # 2. Structure de la table categories
        cursor.execute("PRAGMA table_info(categories)")
        columns = cursor.fetchall()
        print(f"\n📝 Structure de la table categories:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]}) {'PK' if col[5] else ''}")
        
        # 3. Contenu de la table categories
        cursor.execute("SELECT * FROM categories")
        categories = cursor.fetchall()
        
        print(f"\n📊 Catégories sauvegardées ({len(categories)} total):")
        for i, cat in enumerate(categories, 1):
            id_cat, name_cat, url_cat, parent_cat, is_page, created_at, updated_at = cat
            parent = "Racine" if parent_cat is None else f"Fille de '{parent_cat}'"
            page_type = "Produits" if is_page == 1 else "Catégories"
            print(f"   {i}. {id_cat} | {name_cat} | {parent} | {page_type}")
            print(f"      URL: {url_cat}")
            print(f"      Créé: {created_at}")
        
        # 4. Statistiques
        cursor.execute("SELECT COUNT(*) FROM categories")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM categories WHERE parent_cat IS NULL")
        root_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM categories WHERE is_page = 1")
        product_pages = cursor.fetchone()[0]
        
        print(f"\n📈 Statistiques:")
        print(f"   • Total catégories: {total_count}")
        print(f"   • Catégories racines: {root_count}")
        print(f"   • Pages de produits: {product_pages}")
        
        conn.close()
        
        print(f"\n✅ CONCLUSION: La table categories est bien sauvegardée dans la base de données !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    check_database()
