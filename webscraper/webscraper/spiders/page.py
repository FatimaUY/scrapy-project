"""
Script utilitaire de récupération de la page d'accueil de Centrale Brico.
 
Effectue une requête HTTP GET sur ``https://www.centrale-brico.com/`` et
sauvegarde le contenu HTML brut de la réponse dans le fichier ``page.html``
pour inspection locale.
"""

import requests

url = "https://www.centrale-brico.com/"
response = requests.get(url)

with open("page.html", "w", encoding="utf-8") as f:
    f.write(response.text)