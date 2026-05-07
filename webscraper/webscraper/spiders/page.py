"""
Utilitary script to fetch the homepage of Centrale Brico.

Performs an HTTP GET request to ``https://www.centrale-brico.com/`` 
and saves the raw HTML content of the response into the file ``page.html``
for local inspection.
"""

import requests

url = "https://www.centrale-brico.com/"
response = requests.get(url)

with open("page.html", "w", encoding="utf-8") as f:
    f.write(response.text)