import os
import sys
import subprocess


def run_spider(spider):
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