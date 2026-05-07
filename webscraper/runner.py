import os
import sys
import subprocess


"""
Starting point for running Scrapy spiders in the webscraper project.

Provides a command-line entry point to run either 
the category spider, the product spider, or both in sequence, 
while automatically creating the associated log directory for each run.
 
Usage ::
 
    python runner.py [categories | products | all]
"""


def run_spider(spider):
    """
    Exécute un spider Scrapy dans un sous-processus et gère son répertoire de logs.
 
    Crée le répertoire ``logs/scraping/<spider>/`` s'il n'existe pas, puis lance
    la commande ``scrapy crawl <spider>`` via :func:`subprocess.run`.
    En cas d'échec du sous-processus (code de retour non nul), l'erreur est
    affichée mais l'exécution du script se poursuit.
 
    :param spider: Nom du spider Scrapy à exécuter (ex. ``"categoryspider"``
        ou ``"productspider"``).
    """

    log_directory = f"logs/scraping/{spider}"

    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
        print(f"Directory créé : {log_directory}")
    else:
        print(f"Directory already exist.")

    try:
        print(f"\nExecute spider : {spider}\n")
        subprocess.run(["scrapy", "crawl", spider], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\nError, exit script : {e}\n")

    print(f"\nExtraction {spider} finish.\n")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "categories":
        run_spider("categoryspider")

    elif mode == "products":
        run_spider("productspider")

    elif mode == "all":
        run_spider("categoryspider")
        run_spider("productspider")

    else:
        print(f"Mode inconnu : {mode}")
        print("Usage : python runner.py [categories | products | all]")