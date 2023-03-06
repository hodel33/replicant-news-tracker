# Standard modules
import logging

# Custom made modules
from main import NewsScraper


if __name__ == "__main__":
    logging_format = f"------------------\n%(asctime)s\n------------------\n%(message)s\n" # changing the logging format
    logging.basicConfig(filename="scraper_log.txt", level=logging.INFO, format=logging_format, datefmt="%Y-%m-%d %H:%M") # changing the logging format

    ns = NewsScraper()
    ns.scrape_all_sites(pagin_amount=5, debug_mode=False, batch=True)