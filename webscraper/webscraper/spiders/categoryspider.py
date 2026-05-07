"""
Module du spider de scraping des catégories Centrale Brico.
 
Parcourt le menu de navigation principal de ``www.centrale-brico.com``
et produit des :class:`~webscraper.items.CategorieItem` pour chaque
catégorie et sous-catégorie détectée, en conservant la hiérarchie parente.
"""
import scrapy
from webscraper.items import CategorieItem
import datetime


class BricoSpiderSpider(scrapy.Spider):
    """
    Spider d'extraction de l'arborescence des catégories de ``centrale-brico.com``.
 
    Analyse récursivement le menu principal pour construire un arbre de catégories.
    Chaque catégorie est exportée au format CSV et JSON dans le répertoire ``output/``,
    avec un nom de fichier horodaté à la date d'exécution.
 
    L'attribut ``is_page`` vaut ``1`` pour les catégories feuilles (sans sous-menu)
    et ``0`` pour les nœuds intermédiaires.
    """

    
    name = "categoryspider"
    allowed_domains = ["centrale-brico.com"]
    start_urls = ["https://www.centrale-brico.com"]

    today = datetime.date.today()


    custom_settings = {
        "FEEDS": {
            f"output/categories_{today}.csv": {
                "format": "csv",
                "encoding": "utf-8",
                "overwrite": True,
            },
            f"output/categories_{today}.json": {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True,
                "indent": 2,
            },
        }
    }

    def __init__(self):
        """
        Initialise le spider avec les structures de suivi des catégories déjà vues.
 
        ``seen_ids`` évite de traiter deux fois le même nœud de catégorie.
        ``id_to_url`` permet de retrouver l'URL d'une catégorie parente à partir
        de son identifiant HTML.
        """
        self.seen_ids = set()
        self.id_to_url = {} 

    def parse(self, response):
        """
        Analyse la page d'accueil et lance la récursion sur les catégories du menu principal.
 
        :param response: La réponse HTTP de la page d'accueil.
        :return: Un générateur de :class:`~webscraper.items.CategorieItem`.
        """

        categories = response.css('ul.menu-home > li.category')
        yield from self.parse_categories(categories, parent=response.url)

    def parse_categories(self, categories, parent):
        """
        Parcourt récursivement une liste de catégories HTML et produit les items correspondants.
 
        Pour chaque catégorie :
 
        - Si elle possède un sous-menu, ``is_page`` est mis à ``0`` et la méthode
          s'appelle récursivement sur les sous-catégories en passant l'identifiant
          courant comme parent.
        - Si elle est une feuille (pas de sous-menu), ``is_page`` est mis à ``1``.
 
        Les catégories dont l'identifiant a déjà été traité (présent dans ``seen_ids``)
        sont ignorées pour éviter les doublons.
 
        :param categories: Sélecteur Scrapy sur les éléments ``<li class="category">``
            à traiter.
        :param parent: Identifiant ou URL de la catégorie parente, utilisé pour
            renseigner le champ ``parent_cat``.
        :return: Un générateur de :class:`~webscraper.items.CategorieItem`.
        """

        for cat in categories:
            link = cat.css('a[id^="category-"]')

            name_cat = link.css('::text').get()
            url_cat = link.css('::attr(href)').get()
            id_cat = link.css('::attr(id)').get()

            if not (name_cat and id_cat):
                continue

            name_cat = name_cat.strip()

            if id_cat in self.seen_ids:
                continue
            self.seen_ids.add(id_cat)

            self.id_to_url[id_cat] = url_cat

            submenu = cat.xpath('./div[contains(@class,"submenu")]//ul/li[@class="category"]')

            is_page = 0 if submenu else 1

            if parent in self.id_to_url:
                parent_url = self.id_to_url[parent]
            else:
                parent_url = parent  

            item = CategorieItem()
            item["name_cat"] = name_cat
            item["url_cat"] = url_cat
            item["id_cat"] = id_cat
            item["is_page"] = is_page
            item["parent_cat"] = parent_url

            yield item

            if submenu:
                yield from self.parse_categories(submenu, parent=id_cat)