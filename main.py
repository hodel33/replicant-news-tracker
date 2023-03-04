# Standard modules
import sqlite3
import logging
from datetime import datetime
import re
from collections import defaultdict
from itertools import zip_longest

# Importing third-party modules -> requirements.txt
import requests
from bs4 import BeautifulSoup

# Importing custom made modules
import data_init
import sql_mgr as sql
from scraper import WebScraper
from text_processor import TextProcessor


class NewsScraper():

    def __init__(self):

        self.news_sites = data_init.news_sites # the news sites for scraping
        self.headers = data_init.headers # "requests" headers info
        self.db = "sql_data.db" # the database file which will be used
        self.db_init_tables = data_init.db_tables # initializing tables for the database
        self.db_init_cat_kw = data_init.db_categories_keywords # initializing categories and keywords for the database
        self.tp = TextProcessor() # creating an instance of the TextProcessor class
        self.ws = WebScraper() # creating an instance of the WebScraper class

        # acts as a check if the database already has been setup correctly. If the error occurs a new Database with the proper tables will be created and filled with the init data
        try: 
            sql.execute(self.db, "SELECT * FROM keywords LIMIT 1")

        except sqlite3.OperationalError:

            # creates the db automatically and inserts the 3 tables
            for query in self.db_init_tables:
                sql.execute(self.db, query)
            
            # inserts the category + keyword data
            for category, keywords_list in self.db_init_cat_kw.items():
                sql.execute(self.db, f"INSERT INTO categories (category) VALUES ('{category}')")

                cat_id_fetch = sql.execute(self.db, f"SELECT id FROM categories WHERE category='{category}'") # returns a tuple inside a list (fetchall)
                cat_id_fetch = cat_id_fetch[0][0] # to get the actual id number

                for keyword in keywords_list:          
                    sql.execute(self.db, f"INSERT INTO keywords (keyword, category_id) VALUES ('{keyword}', {cat_id_fetch})")

    
    def main(self):

        # scrape all sites
        self.scrape_all(pagin_amount=1, debug_mode=False)

    def scrape_all(self, pagin_amount: int = 1, debug_mode: bool = False):

        article_urls_per_site = []
        all_scraped_articles = []

        total_amount_of_sites = len(self.news_sites)

        # fetch page urls
        for i, site in enumerate(self.news_sites):

            # DEBUG
            # if site["domain"] == "apnews.com" or site["domain"] == "huffpost.com":

            print(f"Scraping {site['domain']} ({i+1}/{total_amount_of_sites} sites)..")

            article_urls_per_site = self.ws.URLScraper(self.headers, site["domain"], site["pages"], site["url_filter"], 
                                                    site["url_exclusion"], site["pagin_filter"], pagin_amount, debug_mode)
            
            all_scraped_articles.append(article_urls_per_site)

        
        # check which article url's we've already scraped from the sql database and store it in a defaultdict for quicker access
        stored_articles = defaultdict(lambda: None) # setting the default value to "None" when creating keys
        for url in [url[0] for url in sql.execute(self.db, "SELECT url FROM articles;")]:
            stored_articles[url]

        # create a new list with only fresh new article urls, which we haven't scraped before
        new_article_urls = [[url for url in urls if url not in stored_articles] for urls in all_scraped_articles]
      
        #print(new_article_urls) # DEBUG

        new_articles = []
        prev_url = ""
        date = str(datetime.now().date()) # save the date together with the article url + text
        curr_article_url_no = 1

        # using zip_longest from itertools we're looping through the nested domain lists zig zag style and applying sleep time if the same 
        # domain is 2 times in a row so we don't push our luck with site banning
        for article_url in zip_longest(*new_article_urls):
            for url in article_url:
                if url is not None:

                    # matching filters for which web site we're trying to scrape
                    scraped_domain = re.sub(r"^https://(www.)?|/.*", "", url)

                    # print(url) # DEBUG
                    # print(scraped_domain) # DEBUG

                    site = next(site for site in self.news_sites if re.sub(r"^https://|/.*", "", site["domain"]) == scraped_domain)

                    div_filter = site["div_filter"]
                    p_attr_exclusion = site["p_attr_exclusion"]

                    # check if the current domain is the same as the last one. [:14] slices a url like this: https://123456 where "123456" are all wildcard chars
                    # also skip article url completely if we didn't get a proper article text
                    try:
                        if url.startswith(prev_url[:14]) and prev_url != "":
                            article_text = self.ws.TextScraper(self.headers, url, div_filter, p_attr_exclusion, sleep=True)
                        else:
                            article_text = self.ws.TextScraper(self.headers, url, div_filter, p_attr_exclusion, sleep=False)

                    except ValueError:
                        continue

                    article_text_cleaned = self.tp.text_cleaner(article_text) # using the text_cleaner() to clean the article text
                    new_articles.append({"url": url, "scrape_date": date, "content": article_text_cleaned})
                    prev_url = url
                    
                    print(f"Scraped URL ({curr_article_url_no}): {url}")
                    curr_article_url_no += 1

        # saving newly scraped articles to the sql database
        for article in new_articles:

            # print(article) # DEBUG

            sql.execute(self.db, 
            f"""INSERT INTO articles
            (url, scrape_date, content)
            VALUES ('{article['url']}', '{article['scrape_date']}', '{article['content']}')""")

        print()
        print(f"Stored {len(new_articles)} new article(s) in the database.")
        


## inserting info
# sql.execute(f"INSERT INTO categories (category) VALUES ('TESTING TESTING')")

## fetching info
# data = sql.execute("SELECT * FROM articles")
# print(data)




if __name__ == "__main__":
    logging_format = f"------------------\n%(asctime)s\n------------------\n%(message)s\n" # changing the logging format
    logging.basicConfig(filename="scraper_log.txt", level=logging.INFO, format=logging_format, datefmt="%Y-%m-%d %H:%M") # changing the logging format

    NewsScraper().main()

