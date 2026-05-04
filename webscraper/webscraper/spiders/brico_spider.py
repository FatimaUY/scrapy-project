import scrapy


class BricoSpiderSpider(scrapy.Spider):
    name = "brico_spider"
    allowed_domains = ["centrale-brico.com"]
    start_urls = ["https://centrale-brico.com"]

    def parse(self, response):

        categories = response.css('a[id^="category-"]')

        for cat in categories:
            nom_cat = cat.css('::text').get().strip()
            lien_cat = cat.css('::attr(href)').get()
            id_cat = cat.css('::attr(id)').get()

            
            print(f"Catégorie trouvée : {id_cat} : {nom_cat} --> {lien_cat}")
            print("-" * 50)

           
        nombre_total = len(categories)
        print(f"Nombre total : {nombre_total}")
           
           
           
        """   
            yield response.follow(lien_categ, callback=self.parse_category, meta={'cat': nom_categ})


    def parse_category(self, response):
        nom_cat = response.meta['cat']
        produits = response.css('h2 a::text, h3 a::text').getall()
        
        for p in produits:
            print(f"[{nom_cat}] Produit trouvé : {p.strip()}")     
    """