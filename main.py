# Standard modules
import os
import re
import sqlite3
import logging
import pandas as pd
from datetime import datetime
from collections import defaultdict
from itertools import zip_longest

# Custom made modules
import data_init # data needed for initializing the app such as site specific scraping info, requests headers info, database tables and keywords/categories for the database
import sql_mgr as sql
from scraper import WebScraper
from text_processor import TextProcessor
from article_statistics import ArticleStatistics
from graph_mgr import GraphManager


class NewsScraper():

    def __init__(self):

        self.news_sites = data_init.news_sites # the news sites for scraping
        self.headers = data_init.headers # "requests" headers info
        self.db = "sql_data.db" # the database file which will be used
        self.export_dir = "exports/"
        self.link_export = "exported_db_article_links.txt" # the text file which will be created for article link exports
        self.db_init_tables = data_init.db_tables # initializing tables for the database
        self.db_init_cat_kw = data_init.db_categories_keywords # initializing categories and keywords for the database
        self.tp = TextProcessor() # creating an instance of the TextProcessor class
        self.ws = WebScraper() # creating an instance of the WebScraper class
        self.clear_terminal = "cls" if os.name == "nt" else "clear" # "nt" (windows), "posix" (linux/mac) / Ternary conditional operator
        
        self.menu_system = {"MAIN MENU": ["Scrape & store data", "Analyze saved data", "Edit identifiers"], 
                       "ANALYZE SAVED DATA": ["Top keywords", "Custom keywords (single/comparison)", "Top categories", "Country mentions", "Export stored article links"], 
                       "EDIT IDENTIFIERS": ["Show keywords/categories", "Add keyword/category", "Delete keyword/category"]}

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


    def validate_user_input(self, word: str) -> bool:
        """
        Check if a keyword/compound keyword is valid. 
        Only alphabetical characters, hyphens "-" and whitespaces " " in between the word(s) are allowed.
        """
        # Remove whitespace at the beginning and end of the word
        word = word.strip()
    
        # Check if the word contains only alphabetical characters, hyphens, or whitespace
        return all(char.isalpha() or char == '-' or char.isspace() for char in word)
            

    def fetch_cat_kw_from_db(self) -> dict:
        '''Fetch the stored identifiers (keyword/categories) from the database'''

        # fetch the stored identifiers (keyword/categories) from the database
        db_cat_kw = sql.execute(self.db, """
                            SELECT category, kw.keyword FROM categories
                            LEFT JOIN keywords kw ON category_id = categories.id;""")
                             
        # importing the identifiers (keyword/categories) into a pandas DataFrame for easier manipulation
        df_cat_kw = pd.DataFrame(db_cat_kw, columns=["category", "keyword"])

        # making a dict from that pandas DataFrame
        dict_cat_kw = df_cat_kw.groupby("category")["keyword"].apply(list).to_dict()

        return dict_cat_kw


    def main(self):

        menu_loop = True

        while menu_loop == True: # Main Menu

            os.system(self.clear_terminal)
            self.print_main_menu()
            input_choice = input(f"    Please select an option: ")

            if input_choice.lower() == "q":
                exit()

            elif input_choice == str(1 + self.menu_system["MAIN MENU"].index("Scrape & store data")):
                self.page_scrape()

            elif input_choice == str(1 + self.menu_system["MAIN MENU"].index("Analyze saved data")):
                stored_articles_count = sql.execute(self.db, "SELECT count(*) FROM articles")
                stored_articles_count = stored_articles_count[0][0]

                if stored_articles_count != 0:
                    self.page_analyze()
                else:
                    input(f"\n    Nothing to analyze (0 articles in db). Please scrape sites and try again.")

            elif input_choice == str(1 + self.menu_system["MAIN MENU"].index("Edit identifiers")):
                self.page_identifiers()

            else: # if the user failed to input one of the valid menu options
                input("\n    Invalid menu option. Press ENTER to try again: ")


    def print_main_header(self):

        print("\033[38;5;133m") # setting a new color for the header

        print(f'''        
    ░█▀▄░█▀▀░█▀█░█░░░▀█▀░█▀▀░█▀█░█▀█░▀█▀░░░█▀█░█▀▀░█░█░█▀▀░░░▀█▀░█▀▄░█▀█░█▀▀░█░█░█▀▀░█▀▄
    ░█▀▄░█▀▀░█▀▀░█░░░░█░░█░░░█▀█░█░█░░█░░░░█░█░█▀▀░█▄█░▀▀█░░░░█░░█▀▄░█▀█░█░░░█▀▄░█▀▀░█▀▄
    ░▀░▀░▀▀▀░▀░░░▀▀▀░▀▀▀░▀▀▀░▀░▀░▀░▀░░▀░░░░▀░▀░▀▀▀░▀░▀░▀▀▀░░░░▀░░▀░▀░▀░▀░▀▀▀░▀░▀░▀▀▀░▀░▀
    © 2023 Hodel33
    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾''')
        print(f"\033[0;0m") # resets the color + new line after showing the whole list


    def print_main_menu(self):

        self.print_main_header()
        print(f"    // MAIN MENU\n")

        for i, menu_item in enumerate(self.menu_system["MAIN MENU"]):
            print(f"    [{i+1}] - {menu_item}")

        print(f"\n    [q] - Exit\n\n")     
        

    def page_scrape(self):

        user_validation_error = True
        while user_validation_error == True: # a while loop until the user inputs the correct value
            os.system(self.clear_terminal)
            self.print_main_header()
            print(f"    // SCRAPE & STORE DATA\n")

            # validating correct user input
            try:
                input_pagin_amount = int(input("\n    Please choose the amount of pagination level (1-15): "))
                if input_pagin_amount < 1 or input_pagin_amount > 15:
                    continue
            except ValueError:
                continue
            user_validation_error = False

            print(f"    ________________________________________")
            print(f"    Scraping sites (pgn level {input_pagin_amount}):")
            print(f"    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")

            self.scrape_all_sites(pagin_amount=input_pagin_amount, debug_mode=False)

            print(f"\n")
            input(f"    Press ENTER to Return to Main Menu: ")
    

    def page_analyze(self):

        # analyze data and plot charts
        st = ArticleStatistics(self.db)
        gm = GraphManager() # using the GraphManager() to print charts

        sub_page_active = False

        while True:

            os.system(self.clear_terminal)
            self.print_main_header()
            print(f"    // ANALYZE SAVED DATA\n")

            if sub_page_active == False:
                for i, menu_item in enumerate(self.menu_system["ANALYZE SAVED DATA"]):
                    print(f"    [{i+1}] - {menu_item}")

                print(f"\n    [q] - Return to Main menu\n\n")
                input_choice = input(f"    Please select an option: ")

            if input_choice.lower() == "q":
                break

            elif input_choice == str(1 + self.menu_system["ANALYZE SAVED DATA"].index("Top keywords")):
                if sub_page_active == False:
                    sub_page_active = True
                    continue

                print(f"    ________________________________________")
                print(f"    Plotting charts for Top keywords:")
                print(f"    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")

                # top keywords
                df_top_keywords = st.get_top_kw()
                saved_files = gm.plot_top_kw_graph(df_top_keywords, 100)
                for file in saved_files:
                    print(f"    {file}")

                print(f"\n")
                input(f"    Press ENTER to continue: ")
                sub_page_active = False

            elif input_choice == str(1 + self.menu_system["ANALYZE SAVED DATA"].index("Custom keywords (single/comparison)")):
                if sub_page_active == False:
                    sub_page_active = True
                    continue
                
                kw_mode = input("\n    Single keyword (1) or Comparison of two keywords (2): ")

                if kw_mode == "1":
                    keyword_1 = input("\n    Please type in the keyword: ").lower().strip()
                    keyword_2 = ""
                elif kw_mode == "2":
                    keyword_1 = input("\n    Please type in the 1st keyword: ").lower().strip()
                    keyword_2 = input("    Please type in the 2nd keyword: ").lower().strip()
                else:
                    input("\n    Invalid option. Press ENTER to try again: ")
                    continue

                kw_1_valid_input_check = True
                kw_2_valid_input_check = True

                # user input validation check (only alphabetical characters, hyphens "-" and whitespaces " " in between the word(s) are allowed.)
                kw_1_valid_input_check = self.validate_user_input(keyword_1)

                if kw_mode == "2":
                    kw_2_valid_input_check = self.validate_user_input(keyword_2)

                if kw_1_valid_input_check == False or kw_2_valid_input_check == False:
                    input("\n    Invalid keyword(s). Only alphabetical characters, dashes '-' and whitespace ' ' in between the word(s) are valid. Press ENTER to try again: ")
                    continue

                print(f"    ________________________________________")
                print(f"    Plotting charts for Custom keyword(s):")
                print(f"    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")
                
                # specific keywords by date
                df_kws_by_date = st.get_kws_by_date(keyword_1, keyword_2)
                saved_files = gm.plot_kws_by_date_graph(df_kws_by_date, keyword_1, keyword_2)

                for file in saved_files:
                    print(f"    {file}")

                print(f"\n")
                input(f"    Press ENTER to continue: ")
                sub_page_active = False

            elif input_choice == str(1 + self.menu_system["ANALYZE SAVED DATA"].index("Top categories")):
                if sub_page_active == False:
                    sub_page_active = True
                    continue

                # top keywords
                print(f"    ________________________________________")
                print(f"    Plotting charts for Top categories:")
                print(f"    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")
                
                # top categories
                df_top_categories = st.get_top_cats()
                saved_files = gm.plot_top_cat_graph(df_top_categories, chart_type="bar")
                for file in saved_files:
                    print(f"    {file}")
                saved_files = gm.plot_top_cat_graph(df_top_categories, chart_type="pie")
                for file in saved_files:
                    print(f"    {file}")

                # categories by date
                df_cats_by_date = st.get_cats_by_date()
                saved_files = gm.plot_cats_by_date_graph(df_cats_by_date)
                for file in saved_files:
                    print(f"    {file}")

                # categories per domain
                df_cats_by_domain = st.get_cats_by_domain()
                saved_files = gm.plot_cats_by_domain_graph(df_cats_by_domain)
                for file in saved_files:
                    print(f"    {file}")

                print(f"\n")
                input(f"    Press ENTER to continue: ")
                sub_page_active = False

            elif input_choice == str(1 + self.menu_system["ANALYZE SAVED DATA"].index("Country mentions")):
                if sub_page_active == False:
                    sub_page_active = True
                    continue

                print(f"    ________________________________________")
                print(f"    Plotting charts for Country mentions:")
                print(f"    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")
                
                # country mentions on heatmap
                df_country_mentions = st.get_country_mentions()
                saved_files = gm.plot_country_mentions_heatmap(df_country_mentions)
                for file in saved_files:
                    print(f"    {file}")

                print(f"\n")
                input(f"    Press ENTER to continue: ")
                sub_page_active = False

            elif input_choice == str(1 + self.menu_system["ANALYZE SAVED DATA"].index("Export stored article links")):
                if sub_page_active == False:
                    sub_page_active = True
                    continue

                # creating a directory for our files if it doesn't exist already
                if not os.path.exists(self.export_dir):
                    os.mkdir(self.export_dir)

                print(f"    ________________________________________")
                print(f"    Exporting article links:")
                print(f"    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")
                
                # fetch the stored article links from the database
                stored_article_urls = []
                for url in [url[0] for url in sql.execute(self.db, "SELECT url FROM articles;")]:
                    stored_article_urls.append(url)

                export_file_path = f"{self.export_dir}{self.link_export}"
                with open(export_file_path, "w") as file:
                    for url in stored_article_urls:
                        file.write(url + "\n")

                print()
                print(f"    Successfully exported all scraped article links to file '{export_file_path}'.")

                print(f"\n")
                input(f"    Press ENTER to continue: ")
                sub_page_active = False

            else: # if the user failed to input one of the valid menu options
                input("\n    Invalid menu option. Press ENTER to try again: ")


    def page_identifiers(self):

        sub_page_active = False

        while True:

            os.system(self.clear_terminal)
            self.print_main_header()
            print(f"    // EDIT IDENTIFIERS\n")

            if sub_page_active == False:
                for i, menu_item in enumerate(self.menu_system["EDIT IDENTIFIERS"]):
                    print(f"    [{i+1}] - {menu_item}")

                print(f"\n    [q] - Return to Main menu\n\n")
                input_choice = input(f"    Please select an option: ")

            if input_choice.lower() == "q":
                break

            elif input_choice == str(1 + self.menu_system["EDIT IDENTIFIERS"].index("Show keywords/categories")):
                if sub_page_active == False:
                    sub_page_active = True
                    continue

                print(f"    ________________________________________")
                print(f"    Listing stored keywords & categories:")
                print(f"    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")
                
                # fetch the stored identifiers (keyword/categories) from the database
                dict_cat_kw = self.fetch_cat_kw_from_db() # returns a dict

                # maximum amount of keywords per row for a nice print
                max_kws_per_row = 10

                # loop over the dictionary and print out the categories and keywords
                for category, keywords in dict_cat_kw.items():
                    
                    print(f"    {category.title()}:") # print the category name in title case

                    if keywords == [None]:
                        print(f"    ''")

                    else:
                        # print the keywords in groups of {max_kws_per_row}
                        for i in range(0, len(keywords), max_kws_per_row):
                            print(" " * 4, end="")
                            print(" ".join(f"'{kw}'" for kw in keywords[i:i+max_kws_per_row]))
                    print()

                print(f"")
                input(f"    Press ENTER to continue: ")
                sub_page_active = False

            elif input_choice == str(1 + self.menu_system["EDIT IDENTIFIERS"].index("Add keyword/category")):
                if sub_page_active == False:
                    sub_page_active = True
                    continue
              
                # fetch the stored identifiers (keyword/categories) from the database
                dict_cat_kw = self.fetch_cat_kw_from_db() # returns a dict

                cat_kw_mode = input("\n    Add a new Category (1) or Keyword (2): ")

                cat_valid_input_check = True
                kw_valid_input_check = True

                # add new Category
                if cat_kw_mode == "1":
                    
                    new_category = input("\n    Please type in the new Category: ").lower().strip()

                    if new_category in dict_cat_kw:
                        input(f"\n    Category '{new_category}' already exists in the database. Press ENTER to try again: ")
                        continue

                    cat_valid_input_check = self.validate_user_input(new_category)

                    if cat_valid_input_check == False:
                        input("\n    Invalid Category name. Only alphabetical characters, dashes '-' and whitespace ' ' in between the word(s) are valid. Press ENTER to try again: ")
                        continue

                    sql.execute(self.db, f"DELETE FROM `sqlite_sequence` WHERE `name` = 'categories';") # reset the AUTOINCR sequence before inserting, so we get the next number
                    sql.execute(self.db, f"INSERT INTO categories (category) VALUES ('{new_category}');") # inserting the new category

                    print()
                    print(f"    Stored the new category '{new_category}' in the database.")
                    print(f"\n")
                    input(f"    Press ENTER to continue: ")

                # add new Keyword
                elif cat_kw_mode == "2":

                    # category name
                    cat_select = input("\n    Please choose which category the new keyword should be added to: ").lower().strip()

                    if cat_select not in dict_cat_kw:
                        input(f"\n    Category '{cat_select}' doesn't exist in the database. Press ENTER to try again: ")
                        continue

                    #category index
                    cat_select_index = sql.execute(self.db, f"SELECT id FROM categories WHERE category = '{cat_select}';")
                    cat_select_index = cat_select_index[0][0]

                    new_keyword = input("    Please type in the new Keyword: ").lower().strip()

                    flat_kw_list = [keyword for sublist in dict_cat_kw.values() for keyword in sublist] # flatten the dict of nested dicts so we get one list with all keywords

                    if new_keyword in flat_kw_list:
                        input(f"\n    Keyword '{new_keyword}' already exists in the database. Press ENTER to try again: ")
                        continue
                    
                    # user input validation check (only alphabetical characters, hyphens "-" and whitespaces " " in between the word(s) are allowed.)
                    # add new Keyword check
                    kw_valid_input_check = self.validate_user_input(new_keyword)

                    if kw_valid_input_check == False:
                        input("\n    Invalid Keyword name. Only alphabetical characters, dashes '-' and whitespace ' ' in between the word(s) are valid. Press ENTER to try again: ")
                        continue

                    sql.execute(self.db, f"DELETE FROM `sqlite_sequence` WHERE `name` = 'keywords';") # reset the AUTOINCR sequence before inserting, so we get the next number
                    sql.execute(self.db, f"INSERT INTO keywords (keyword, category_id) VALUES ('{new_keyword}', {cat_select_index});") # inserting the new keyword

                    print()
                    print(f"    Stored the new keyword '{new_keyword}' to category '{cat_select}' in the database.")
                    print(f"\n")
                    input(f"    Press ENTER to continue: ")
                
                else:
                    input("\n    Invalid option. Press ENTER to try again: ")
                    continue

                sub_page_active = False

            elif input_choice == str(1 + self.menu_system["EDIT IDENTIFIERS"].index("Delete keyword/category")):
                pass

            else: # if the user failed to input one of the valid menu options
                input("\n    Invalid menu option. Press ENTER to try again: ")


    def scrape_all_sites(self, pagin_amount: int = 1, debug_mode: bool = False, batch: bool = False):

        article_urls_per_site = []
        all_scraped_articles = []

        total_amount_of_sites = len(self.news_sites)

        # fetch page urls
        for i, site in enumerate(self.news_sites):

            print(f"    Scraping {site['domain']} ({i+1}/{total_amount_of_sites} sites)..")

            article_urls_per_site = self.ws.URLScraper(self.headers, site["domain"], site["pages"], site["url_filter"], 
                                                    site["url_exclusion"], site["pagin_filter"], pagin_amount, debug_mode)
            
            all_scraped_articles.append(article_urls_per_site)

        # check which article urls we've already scraped from the sql database and store it in a defaultdict for quicker access
        stored_articles = defaultdict(lambda: None) # setting the default value to "None" when creating keys
        for url in [url[0] for url in sql.execute(self.db, "SELECT url FROM articles;")]:
            stored_articles[url]

        # create a new list with only fresh new article urls, which we haven't scraped before
        new_article_urls = [[url for url in urls if url not in stored_articles] for urls in all_scraped_articles]
      
        new_articles = []
        prev_url = ""
        date = str(datetime.now().date()) # save the date together with the article url + text
        curr_article_url_no = 1

        print(f"    ________________________________________")
        print(f"    Scraping articles:")
        print(f"    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")

        # using zip_longest from itertools we're looping through the nested domain lists zig zag style and applying sleep time if the same 
        # domain is 2 times in a row so we don't push our luck with site banning
        for article_url in zip_longest(*new_article_urls):
            for url in article_url:
                if url is not None:

                    # matching filters for which web site we're trying to scrape
                    scraped_domain = re.sub(r"^https://(www.)?|/.*", "", url)

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
                    
                    print(f"    Scraped URL ({curr_article_url_no}): {url}")
                    curr_article_url_no += 1

        # saving newly scraped articles to the sql database
        for article in new_articles:

            sql.execute(self.db, 
            f"""INSERT INTO articles
            (url, scrape_date, content)
            VALUES ('{article['url']}', '{article['scrape_date']}', '{article['content']}')""")

        print()
        print(f"    Stored {len(new_articles)} new article(s) in the database.")

        # if run from batch script - save the amount stored to a file
        if batch:
            now = datetime.now()
            scheduled_message = f"Stored {len(new_articles)} new article(s) in the database."
            scheduled_format = f"------------------\n{now.strftime('%Y-%m-%d %H:%M')}\n------------------\n{scheduled_message}\n\n"
            with open("scheduled_scraper.txt", "a") as file:
                    file.write(scheduled_format)
        

if __name__ == "__main__":
    logging_format = f"------------------\n%(asctime)s\n------------------\n%(message)s\n" # changing the logging format
    logging.basicConfig(filename="scraper_log.txt", level=logging.INFO, format=logging_format, datefmt="%Y-%m-%d %H:%M") # changing the logging format

    NewsScraper().main()