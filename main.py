# Standard modules
import os
import re
import shutil
import sqlite3
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from itertools import zip_longest

# Third-party modules -> requirements.txt
import requests

# Custom made modules
import data_init # data needed for initializing the app such as site specific scraping info, requests headers info, database tables and keywords/categories for the database
import sqlite_x33 as sql
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
                       "ANALYZE SAVED DATA": ["Top keywords", "Custom keywords (single/comparison)", "Top categories", "Country mentions", "Export stored article links", "Scrape statistics"], 
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
                            SELECT categories.id, category, kw.keyword FROM categories
                            LEFT JOIN keywords kw ON category_id = categories.id;""")
    
        # Create an empty dictionary to hold the results
        dict_cat_kw = {}
        
        # Populate the dictionary
        for cat_id, cat_name, keyword in db_cat_kw:

            if cat_name not in dict_cat_kw:
                dict_cat_kw[cat_name] = {'id': cat_id, 'keywords': []}
            
            if keyword:
                dict_cat_kw[cat_name]['keywords'].append(keyword)
        
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
            print(f"    // SCRAPE & STORE DATA")

            input_pagin_amount = input("\n    Please choose the amount of pagination level [1-15] (ENTER to cancel): ")

            # If the input is a digit, convert it to the corresponding category name
            if input_pagin_amount.isdigit():
                input_pagin_amount = int(input_pagin_amount)
                if input_pagin_amount < 1 or input_pagin_amount > 15:
                    input("\n    Invalid amount. Must be a number between 1-15. Press ENTER to try again: ")
                    continue

            elif not input_pagin_amount:
                break

            else:
                input("\n    Invalid input. Must be a number between 1-15. Press ENTER to try again: ")
                continue

            user_validation_error = False

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
                print(f"    Calculating data..")
                df_top_keywords = st.get_top_kw()
                print(f"    Plotting graphs..")
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
                
                kw_mode = input("\n    Single keyword [1] or Comparison of two keywords [2] (ENTER to cancel): ")

                if not kw_mode:
                    sub_page_active = False
                    continue
                elif kw_mode == "1":
                    keyword_1 = input("\n    Please type in a custom keyword (ENTER to cancel): ").lower().strip()
                    if not keyword_1:
                        continue
                    keyword_2 = ""
                elif kw_mode == "2":
                    keyword_1 = input("\n    Please type in the 1st custom keyword (ENTER to cancel): ").lower().strip()
                    if not keyword_1:
                        continue
                    keyword_2 = input("    Please type in the 2nd custom keyword (ENTER to cancel): ").lower().strip()
                    if not keyword_2:
                        continue
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
                print(f"    Calculating data..")
                df_kws_by_date = st.get_kws_by_date(keyword_1, keyword_2)
                print(f"    Plotting graphs..")
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
                print(f"    Calculating data..")
                df_top_categories = st.get_top_cats()
                print(f"    Plotting graphs..")
                saved_files = gm.plot_top_cat_graph(df_top_categories, chart_type="bar")
                for file in saved_files:
                    print(f"    {file}")
                print(f"    Plotting graphs..")
                saved_files = gm.plot_top_cat_graph(df_top_categories, chart_type="pie")
                for file in saved_files:
                    print(f"    {file}")

                print()

                # categories by date
                print(f"    Calculating data..")
                df_cats_by_date = st.get_cats_by_date()
                print(f"    Plotting graphs..")
                saved_files = gm.plot_cats_by_date_graph(df_cats_by_date)
                for file in saved_files:
                    print(f"    {file}")

                print()

                # categories per domain
                print(f"    Calculating data..")
                df_cats_by_domain = st.get_cats_by_domain()
                print(f"    Plotting graphs..")
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
                print(f"    Calculating data..")
                df_country_mentions = st.get_country_mentions()
                print(f"    Plotting graphs..")
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

            elif input_choice == str(1 + self.menu_system["ANALYZE SAVED DATA"].index("Scrape statistics")):
                if sub_page_active == False:
                    sub_page_active = True
                    continue

                print(f"    ________________________________________")
                print(f"    Scrape statistics:")
                print(f"    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")

                # Retrieve and calculate the detailed statistics here
                stats = st.get_detailed_statistics()
                total_articles = stats['total_articles']
                formatted_total_articles = "{:,}".format(total_articles).replace(",", ".")
                unique_scrape_days = stats['unique_scrape_days']
                time_period = stats['time_period']
                articles_per_domain = stats['articles_per_domain']

                print()
                print(f"    Total number of Scraped Articles: {formatted_total_articles}")
                print(f"    Number of actual Scraping Days: {unique_scrape_days}")
                print(f"    Scraping Time Period: {time_period['from_date']} -> {time_period['to_date']}\n")

                print(f"    Articles per Domain:")
                for domain, count in articles_per_domain.items():
                    print(f"    - '{domain}' : {count}")

                print(f"\n")
                input(f"    Press ENTER to continue: ")
                sub_page_active = False

            else: # if the user failed to input one of the valid menu options
                input("\n    Invalid menu option. Press ENTER to try again: ")


    def page_identifiers(self):

        sub_page_active = False
        retry_cat_kw = None
        retry_cat_pre_select = None

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

                # Get terminal width; fallback to (100, 24) if unable to determine
                terminal_width, _ = shutil.get_terminal_size((100, 24))

                # loop over the dictionary and print out the categories and keywords
                for category, details in dict_cat_kw.items():
                    cat_id = details['id']
                    keywords = details['keywords']

                    print(f"    [{cat_id}] {category.title()}")
                    print()

                    if not keywords:
                        print(f"    (no keywords available)")
                    else:
                        line = " " * 4  # initial indentation
                        for kw in keywords:
                            kw_str = f"'{kw}' "
                            if len(line + kw_str) > terminal_width:
                                print(line)
                                line = " " * 4  # reset the line with initial indentation
                            line += kw_str
                        print(line)  # print remaining keywords
                        
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

                # Create a dictionary that maps IDs to category names
                id_to_category = {details['id']: category for category, details in dict_cat_kw.items()}

                if retry_cat_kw == None:
                    cat_kw_mode = input("\n    Add a new Category [1] or Keyword [2] (ENTER to cancel): ")
                elif retry_cat_kw == "new_cat":
                    print(("\n    Add a new Category [1] or Keyword [2] (ENTER to cancel): 1"))
                    cat_kw_mode = "1"
                elif retry_cat_kw == "new_kw":
                    print(("\n    Add a new Category [1] or Keyword [2] (ENTER to cancel): 2"))
                    cat_kw_mode = "2"

                if not cat_kw_mode:
                    sub_page_active = False
                    continue

                # add new Category
                if cat_kw_mode == "1":

                    print()
                    print(f"    Existing categories:")

                    # loop over the dictionary and print out the categories and keywords
                    for category, details in dict_cat_kw.items():
                        cat_id = details['id']
                        print(f"    [{cat_id}] {category.title()}")
                    
                    new_category = input("\n    Please type in the new category (ENTER to cancel): ").lower().strip()

                    if not new_category:
                        retry_cat_kw = None
                        continue

                    if new_category in dict_cat_kw:
                        input(f"\n    Category '{new_category.title()}' already exists in the database. Press ENTER to try again: ")
                        retry_cat_kw = "new_cat"
                        continue

                    if not self.validate_user_input(new_category):
                        input("\n    Invalid name. Only letters, dashes, and spaces allowed. Press ENTER to retry: ")
                        retry_cat_kw = "new_cat"
                        continue

                    sql.execute(self.db, f"DELETE FROM `sqlite_sequence` WHERE `name` = 'categories';") # reset the AUTOINCR sequence before inserting, so we get the next number
                    sql.execute(self.db, f"INSERT INTO categories (category) VALUES ('{new_category}');") # inserting the new category

                    print()
                    print(f"    Stored the new category '{new_category.title()}' in the database.")
                    print(f"\n")
                    input(f"    Press ENTER to continue: ")
                    sub_page_active = False

                # add new Keyword
                elif cat_kw_mode == "2":

                    print()
                    print(f"    Existing categories:")

                    # loop over the dictionary and print out the categories
                    for category, details in dict_cat_kw.items():
                        cat_id = details['id']
                        print(f"    [{cat_id}] {category.title()}")

                    if not retry_cat_pre_select:
                        # category name
                        cat_select = input("\n    Specify the category for keyword addition (ENTER to cancel): ").lower().strip()
                    else:
                        cat_select = retry_cat_pre_select
                        print(f"\n    Specify the category for keyword addition (ENTER to cancel): {cat_select.title()}")

                    # If the input is a digit, convert it to the corresponding category name
                    if cat_select.isdigit():
                        cat_id = int(cat_select)
                        if cat_id in id_to_category:
                            cat_select = id_to_category[cat_id]
                        else:
                            input(f"\n    Category ID '{cat_select.title()}' doesn't exist in the database. Press ENTER to try again: ")
                            retry_cat_kw = "new_kw"
                            continue
                    
                    elif not cat_select:
                        retry_cat_kw = None
                        continue
                    
                    elif cat_select not in dict_cat_kw:
                        input(f"\n    Category '{cat_select.title()}' doesn't exist in the database. Press ENTER to try again: ")
                        retry_cat_kw = "new_kw"
                        continue

                    # category index
                    cat_select_index = dict_cat_kw[cat_select]['id']

                    print()
                    print(f"    Existing keywords in category '{cat_select.title()}':")

                    # List keywords under the selected category
                    keywords = dict_cat_kw[cat_select]['keywords']

                    for idx, keyword in enumerate(keywords):
                        print(f"    [{idx + 1}] {keyword.title()}")

                    new_keyword = input("\n    Please type in the new keyword (ENTER to cancel): ").lower().strip()

                    # Check if the keyword is an empty string.
                    if not new_keyword:
                        retry_cat_kw = "new_kw"
                        retry_cat_pre_select = None
                        continue

                    # flatten all keywords into one list
                    flat_kw_list = [keyword for details in dict_cat_kw.values() for keyword in details['keywords']]

                    if new_keyword in flat_kw_list:
                        input(f"\n    Keyword '{new_keyword}' already exists in the database. Press ENTER to try again: ")
                        retry_cat_kw = "new_kw"
                        retry_cat_pre_select = cat_select
                        continue
                    
                    # user input validation check (only alphabetical characters, hyphens "-" and whitespaces " " in between the word(s) are allowed.)
                    # add new Keyword check
                    if not self.validate_user_input(new_keyword):
                        input("\n    Invalid name. Only letters, dashes, and spaces allowed. Press ENTER to retry: ")
                        retry_cat_kw = "new_kw"
                        retry_cat_pre_select = cat_select
                        continue

                    sql.execute(self.db, f"DELETE FROM `sqlite_sequence` WHERE `name` = 'keywords';") # reset the AUTOINCR sequence before inserting, so we get the next number
                    sql.execute(self.db, f"INSERT INTO keywords (keyword, category_id) VALUES ('{new_keyword}', {cat_select_index});") # inserting the new keyword

                    print()
                    print(f"    Stored the new keyword '{new_keyword.title()}' to category '{cat_select.title()}' in the database.")
                    print(f"\n")
                    input(f"    Press ENTER to continue: ")
                    retry_cat_pre_select = None
                    sub_page_active = False
                
                else:
                    input("\n    Invalid option. Press ENTER to try again: ")
                    continue

            elif input_choice == str(1 + self.menu_system["EDIT IDENTIFIERS"].index("Delete keyword/category")):
                
                if sub_page_active == False:
                    sub_page_active = True
                    continue

                # Fetch the stored identifiers (keyword/categories) from the database
                dict_cat_kw = self.fetch_cat_kw_from_db()  # returns a dict

                # Create a dictionary that maps IDs to category names
                id_to_category = {details['id']: category for category, details in dict_cat_kw.items()}

                if retry_cat_kw == None:
                    cat_kw_mode = input("\n    Delete a Category [1] or Keyword [2] (ENTER to cancel): ")
                elif retry_cat_kw == "del_cat":
                    print(("\n    Delete a Category [1] or Keyword [2] (ENTER to cancel): 1"))
                    cat_kw_mode = "1"
                elif retry_cat_kw == "del_kw":
                    print(("\n    Delete a Category [1] or Keyword [2] (ENTER to cancel): 2"))
                    cat_kw_mode = "2"

                if not cat_kw_mode:
                    sub_page_active = False
                    continue

                # Delete Category
                if cat_kw_mode == "1":

                    print()
                    print(f"    Existing categories:")

                    # Loop over the dictionary and print out the categories
                    for category, details in dict_cat_kw.items():
                        cat_id = details['id']
                        print(f"    [{cat_id}] {category.title()}")

                    del_category = input("\n    Specify the ID or name of the category to delete (ENTER to cancel): ").strip()

                    # If the input is a digit, convert it to the corresponding category name
                    if del_category.isdigit():
                        cat_id = int(del_category)
                        if cat_id in id_to_category:
                            del_category = id_to_category[cat_id]
                        else:
                            input(f"\n    Category ID '{del_category}' doesn't exist in the database. Press ENTER to try again: ")
                            retry_cat_kw = "del_cat"
                            continue
                    
                    elif not del_category:
                        retry_cat_kw = None
                        continue

                    elif del_category not in dict_cat_kw:
                        input(f"\n    Category '{del_category.title()}' doesn't exist in the database. Press ENTER to try again: ")
                        retry_cat_kw = "del_cat"
                        continue

                    # Deleting the category from the database
                    sql.execute(self.db, f"DELETE FROM categories WHERE category = '{del_category}';")

                    print()
                    print(f"    Deleted the category '{del_category.title()}' from the database.")
                    print(f"\n")
                    input(f"    Press ENTER to continue: ")
                    sub_page_active = False

                # Delete Keyword
                elif cat_kw_mode == "2":

                    print()
                    print(f"    Existing categories:")

                    # Loop over the dictionary and print out the categories
                    for category, details in dict_cat_kw.items():
                        cat_id = details['id']
                        print(f"    [{cat_id}] {category.title()}")

                    if not retry_cat_pre_select:
                        # category name
                        cat_select = input("\n    Specify the ID or name of the category for keyword deletion (ENTER to cancel): ").lower().strip()
                    else:
                        cat_select = retry_cat_pre_select
                        print(f"\n    Specify the ID or name of the category for keyword deletion (ENTER to cancel): {cat_select.title()}")

                    # If the input is a digit, convert it to the corresponding category name
                    if cat_select.isdigit():
                        cat_id = int(cat_select)
                        if cat_id in id_to_category:
                            cat_select = id_to_category[cat_id]
                        else:
                            input(f"\n    Category ID '{cat_select}' doesn't exist in the database. Press ENTER to try again: ")
                            continue
                    
                    elif not cat_select:
                        retry_cat_kw = None
                        continue
                    
                    elif cat_select not in dict_cat_kw:
                        input(f"\n    Category '{cat_select.title()}' doesn't exist in the database. Press ENTER to try again: ")
                        retry_cat_kw = "del_kw"
                        continue

                    print()
                    print(f"    Existing keywords in category '{cat_select.title()}':")

                    # List keywords under the selected category
                    keywords = dict_cat_kw[cat_select]['keywords']

                    # Create a dictionary that maps IDs to keywords for a selected category
                    id_to_keyword = {idx + 1: keyword for idx, keyword in enumerate(keywords)}

                    for idx, keyword in enumerate(keywords):
                        print(f"    [{idx + 1}] {keyword.title()}")

                    del_keyword = input("\n    Specify the ID or name of the keyword to delete (ENTER to cancel): ").strip()

                    # If the input is a digit, convert it to the corresponding keyword name
                    if del_keyword.isdigit():
                        del_keyword = int(del_keyword)
                        if del_keyword in id_to_keyword:
                            del_keyword = id_to_keyword[del_keyword]
                        else:
                            input(f"\n    Keyword ID '{del_keyword}' doesn't exist in the database. Press ENTER to try again: ")
                            retry_cat_kw = "del_kw"
                            retry_cat_pre_select = cat_select
                            continue
                    
                    elif not del_keyword:
                        retry_cat_kw = "del_kw"
                        retry_cat_pre_select = None
                        continue
                    
                    elif del_keyword not in keywords:
                        input(f"\n    Keyword '{del_keyword.title()}' doesn't exist in the database. Press ENTER to try again: ")
                        retry_cat_kw = "del_kw"
                        retry_cat_pre_select = cat_select
                        continue

                    # Deleting the keyword from the database
                    sql.execute(self.db, f"DELETE FROM keywords WHERE keyword = '{del_keyword}' AND category_id = (SELECT id FROM categories WHERE category = '{cat_select}');")

                    print()
                    print(f"    Deleted the keyword '{del_keyword}' from category '{cat_select.title()}' in the database.")
                    print(f"\n")
                    input(f"    Press ENTER to continue: ")
                    retry_cat_pre_select = None
                    sub_page_active = False

                else:
                    input("\n    Invalid option. Press ENTER to try again: ")
                    continue

            else: # if the user failed to input one of the valid menu options
                input("\n    Invalid menu option. Press ENTER to try again: ")


    def scrape_domains(self, pagin_amount, debug_mode):

        total_amount_of_sites = len(self.news_sites)

        # Fetch existing URLs from scrape_que, articles, and exclude_articles into a set
        all_existing_urls = set(url[0] for url in sql.execute(self.db, """
            SELECT url FROM scrape_que
            UNION
            SELECT url FROM articles
            UNION
            SELECT url FROM exclude_articles;
        """))

        # self.news_sites = [site for site in self.news_sites if site['domain'] == 'apnews.com'] # DEBUG
        
        # fetch page urls
        for i, site in enumerate(self.news_sites):
            
            print(f"    Scraping {site['domain']} ({i+1}/{total_amount_of_sites} sites)..")

            try:
                article_urls_per_site = self.ws.URLScraper(self.headers, site["domain"], site["pages"], site["url_filter"], 
                                                    site["url_exclusion"], site["pagin_filter"], pagin_amount, debug_mode)
                
                # Filter out URLs already in the scrape_que
                new_article_urls_per_site = [url for url in article_urls_per_site if url not in all_existing_urls]
                
                # Insert the scraped URLs into the scrape_que table only if they don't already exist
                for url in new_article_urls_per_site:

                        scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        sql.execute(self.db, 
                                    f"""INSERT INTO scrape_que
                                    (url, scrape_time, scrape_retries)
                                    VALUES ('{url}', '{scrape_time}', 0);""")
            
            except Exception as e:
                logging.error(f"Error while scraping {site['domain']}: {e}")
                continue


    def scrape_article_urls(self, debug_mode):

        # Remove any scrape_que urls that are already in either articles or exclude_articles
        sql.execute(self.db, """DELETE FROM scrape_que
                                 WHERE url IN (SELECT url FROM articles)
                                    OR url IN (SELECT url FROM exclude_articles);""")

        # Reset the AUTOINCR sequence before inserting
        sql.execute(self.db, f"DELETE FROM `sqlite_sequence` WHERE `name` = 'scrape_que';") 

        # Fetch URLs from the table
        all_scraped_article_urls = sql.execute(self.db, "SELECT url FROM scrape_que;")

        # Extract URLs into a list
        all_scraped_article_urls = [row[0] for row in all_scraped_article_urls]

        total_new_articles_count = len(all_scraped_article_urls)

        # Create a defaultdict to hold URLs grouped by domain
        urls_by_domain = defaultdict(list)

        # Populate the defaultdict
        for url in all_scraped_article_urls:
            domain = re.sub(r"^https://(www.)?|/.*", "", url)
            urls_by_domain[domain].append(url)

        # Convert the defaultdict to a list of lists
        sorted_article_urls = list(urls_by_domain.values())
        
        prev_url = ""
        date = str(datetime.now().date()) # save the date together with the article url + text
        curr_article_url_no = 0
        urls_not_saved = 0

        for article_url in zip_longest(*sorted_article_urls):
            for url in article_url:
                if url is not None:

                    # matching filters for which web site we're trying to scrape
                    scraped_domain = re.sub(r"^https://(www.)?|/.*", "", url)
                    
                    site = next(site for site in self.news_sites if re.sub(r"^https://|/.*", "", site["domain"]) == scraped_domain)
                    
                    div_filter = site["div_filter"]
                    p_attr_exclusion = site["p_attr_exclusion"]

                    # Increment the scrape_retries count for the current URL in the scrape_que table
                    sql.execute(self.db, f"UPDATE scrape_que SET scrape_retries = scrape_retries + 1 WHERE url='{url}';")

                    # check if the current domain is the same as the last one. [:14] slices a url like this: https://123456 where "123456" are all wildcard chars
                    # also skip article url completely if we didn't get a proper article text
                    try:
                        if url.startswith(prev_url[:14]) and prev_url != "":
                            article_text = self.ws.TextScraper(self.headers, url, div_filter, p_attr_exclusion, debug_mode, sleep=True)
                        else:
                            article_text = self.ws.TextScraper(self.headers, url, div_filter, p_attr_exclusion, debug_mode, sleep=False)

                    except requests.exceptions.RequestException:
                        urls_not_saved += 1
                        continue
                   
                    except ValueError as ve:
                        # Log the failure and its reason to the database
                        sql.execute(self.db, 
                                    f"""INSERT INTO exclude_articles
                                    (url, reason)
                                    VALUES ('{url}', '{str(ve)}')""")
                        
                        # Remove the URL from the scrape_que
                        sql.execute(self.db, f"DELETE FROM scrape_que WHERE url='{url}';")

                        urls_not_saved += 1
                        continue
                        
                    # clean the article text from stopwords etc
                    article_text_cleaned = self.tp.text_cleaner(article_text)

                    # Save the cleaned article text directly to the database
                    sql.execute(self.db, 
                                f"""INSERT INTO articles
                                (url, scrape_date, content)
                                VALUES ('{url}', '{date}', '{article_text_cleaned}')""")
                    
                    # Remove the URL from the scrape_que
                    sql.execute(self.db, f"DELETE FROM scrape_que WHERE url='{url}';")
                    
                    curr_article_url_no += 1
                    prev_url = url

                    print(f"    Scraped URL ({curr_article_url_no}/{total_new_articles_count}): {url}")
                    
        return curr_article_url_no, urls_not_saved


    def scrape_all_sites(self, pagin_amount: int = 1, debug_mode: bool = True, batch: bool = False):

        if self.full_scrape_needed(time_threshold_in_hours=1):

            print(f"    ________________________________________")
            print(f"    Scraping sites (pgn level {pagin_amount}):")
            print(f"    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")

            self.scrape_domains(pagin_amount, debug_mode)

        print(f"    ________________________________________")
        print(f"    Scraping articles:")
        print(f"    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")
        
        curr_article_url_no, urls_not_saved = self.scrape_article_urls(debug_mode)
        
        print()
        print(f"    Successfully stored {curr_article_url_no} new article(s) in the database ({urls_not_saved} were omitted).")

        # if run from batch script - save the amount stored to a file
        if batch:
            now = datetime.now()
            scheduled_message = f"Successfully stored {curr_article_url_no} new article(s) in the database ({urls_not_saved} were omitted)."
            scheduled_format = f"------------------\n{now.strftime('%Y-%m-%d %H:%M')}\n------------------\n{scheduled_message}\n\n"
            with open("scheduled_scraper.txt", "a") as file:
                    file.write(scheduled_format)


    def full_scrape_needed(self, time_threshold_in_hours=1) -> bool:

        scrape_time_limit = datetime.now() - timedelta(hours=time_threshold_in_hours)
        
        # Fetch URLs and their scrape_time from the table
        scrape_que = sql.execute(self.db, "SELECT url, scrape_time FROM scrape_que;")
        
        # If the table is empty, return True
        if not scrape_que:
            return True
        
        # Get the newest URL's time
        newest_url_time = max(scrape_que, key=lambda x: datetime.strptime(x[1], "%Y-%m-%d %H:%M:%S"))[1]
        newest_url_time = datetime.strptime(newest_url_time, "%Y-%m-%d %H:%M:%S")
        
        return newest_url_time < scrape_time_limit
        

if __name__ == "__main__":

    logging_format = f"------------------\n%(asctime)s\n------------------\n%(message)s\n" # changing the logging format
    logging.basicConfig(filename="scraper_log.txt", level=logging.INFO, format=logging_format, datefmt="%Y-%m-%d %H:%M") # changing the logging format

    NewsScraper().main()