# Standard modules
import re
import logging
import pandas as pd
from tqdm import tqdm
import sqlite_x33 as sql
from collections import defaultdict

# Third-party modules -> requirements.txt
from country_names import CountryNames

# Custom made modules
from graph_mgr import GraphManager


class ArticleStatistics():
    """Uses Pandas to sift through and analyze data."""

    def __init__(self, database):

        self.db = database
        self.db_articles = sql.execute(self.db, "SELECT * FROM articles;") # articles from the sql database
        self.df_articles = pd.DataFrame(self.db_articles, columns=["url", "date", "text"]) # DataFrame from articles table in sql database
        self.article_texts_list = [article[2].split() for article in self.db_articles] # a list of all article words, not changing their original order within the texts
        self.articles_words_list = [word for lst in self.article_texts_list for word in lst] # all articles' words in a list

        # text filters (keyword/categories) from the database
        self.db_cat_kw = sql.execute(self.db, """
                                  SELECT keyword, cat.category FROM keywords
                                  JOIN categories cat ON category_id = cat.id;""")
        
        # saving separate lists for keywords - 1 for single keywords and 1 for multiple keywords (phrases)
        # this technique a is used to speed up performance. It's a lot slower if we only go on a general filtering of both types
        self.single_kw = [(keyword, category) for keyword, category in self.db_cat_kw if " " not in keyword] # keywords consisting of a single word
        self.phrase_kw = [(keyword, category) for keyword, category in self.db_cat_kw if " " in keyword] # phrases consisting of multiple words

        # saving separate lists for country names - 1 for full info, 1 for single country names and 1 for multiple country names
        self.countries = [(country.lower(), data['iso3']) for country, data in CountryNames().get_dict().items()]
        self.countries_multi = [(country.lower(), data['iso3']) for country, data in CountryNames().get_dict().items() if " " in country]

        # custom tqdm loading bar format
        self.custom_bar = "    [{bar:30}] {percentage:3.0f}%  "
        tqdm.pandas(bar_format=self.custom_bar, ascii=" =", leave=False)


    def _classify_text(self, text) -> str:
        """Decides the main category of a text based on keyword hits."""

        ## Phrase hits - direct search in the articles
        category_hits = defaultdict(int)
        for phrase, category in self.phrase_kw:
            category_hits[category] += len(re.findall(phrase, text))

        ## Keyword hits - reverse search in the articles, starting with a count of unique keywords in the actual articles
        # Get a word count of unique words in all articles.
        article_words = text.split()
        for keyword, category in self.single_kw:
            category_hits[category] += article_words.count(keyword)

        # Determine the most common category among the keyword hits
        category, count = list(category_hits.keys()), list(category_hits.values())
        main_category = [category[count.index(max(count))]][0] # getting the dict key (category) which has the highest amount of hits (keywords)

        return main_category # Return the category with the most hits.
    

    def _count_occurences(self, text: str, kw: str) -> int:
        """Counts the amount of occurences of the given keyword."""

        keyword = kw
        keyword_hits = defaultdict(int)

        ## Phrase hits (multiple words) - direct search in the articles
        if " " in kw:
            pattern = fr"\b{keyword}\b"
            keyword_hits["kw_count"] += len(re.findall(pattern, text))

        ## Keyword hits - reverse search in the articles, starting with a count of unique keywords in the actual articles
        # Get a word count of unique words in all articles.
        else:
            article_words = text.split()
            keyword_hits["kw_count"] += article_words.count(keyword)

        return keyword_hits # Return the amount of occurences of the given keyword


    def get_top_kw(self) -> pd.DataFrame:
        """Counts keyword hits in all articles, using different methods for single word keywords and multiple word phrases, for optimal speed."""

        ## Phrase hits (multiple keywords) - counting phrase hits in all articles.
        phrases_hit_count = defaultdict(int)
        for article in tqdm(self.df_articles["text"], bar_format=self.custom_bar, ascii=" =", leave=False):
            for phrase, _ in self.phrase_kw:
                phrases_hit_count[phrase] += len(re.findall(phrase, article))
        df_phrases_hits = pd.DataFrame(phrases_hit_count.items(), columns=["phrase", "count"])

        ## Single keyword hits - counting unique words in all articles.
        words_count = defaultdict(int)
        for word in tqdm(self.articles_words_list, bar_format=self.custom_bar, ascii=" =", leave=False):
            words_count[word] += 1
        df_all_articles_words_count = pd.DataFrame(words_count.items(), columns=["word", "count"])

        # Dataframe of the keywords/categories from the sql database
        df_keywords = pd.DataFrame(self.db_cat_kw, columns=["keyword", "category"])

        # By merging keywords table with article words counts, we get a DF with single keyword hit counts
        df_singles_result = df_keywords.merge(df_all_articles_words_count, left_on="keyword", right_on="word")
        del df_singles_result["word"]

        # By merging keywords table with phrases hit counts, we get a DF of all phrases hit counts.
        df_phrases_result = df_keywords.merge(df_phrases_hits, left_on="keyword", right_on="phrase")
        del df_phrases_result["phrase"]

        ## Finalize data - combining data for both single keyword + multiple keywords (phrases)

        # Adding together the hit count DFs for both phrases and single keywords
        df_output = pd.concat([df_singles_result, df_phrases_result])
        df_output = df_output.sort_values(by=["count"], ascending=False)  # Sort DataFrame by "count"
        df_output = df_output.reset_index(level=0, drop=True)
       
        return df_output


    def get_top_cats(self) -> pd.DataFrame:
        """Counts articles per category and groups by date."""

        categorized_articles = defaultdict(int)
        for article in tqdm(self.df_articles["text"], bar_format=self.custom_bar, ascii=" =", leave=False):

            main_category = self._classify_text(article) # Run _classify_text on the article, getting the most prominent category for the article.
            categorized_articles[main_category] += 1

        ## Finalize data - create a final "output" dataframe
        df_output = pd.DataFrame(categorized_articles.items(), columns=["category", "count"])
        df_output = df_output.sort_values(by="count", ascending=False) # Sort DataFrame by "count"
        df_output = df_output.reset_index(level=0, drop=True)

        return df_output


    def get_cats_by_date(self) -> pd.DataFrame:
        """Counts articles per category and date (scrape-date)"""

        # Make a working copy of the articles dataframe, leaving out the url column.
        df_articles = self.df_articles[["date", "text"]]
        
        # Run the text classifier on each article and add the main category to the new "label" column.
        df_articles["category"] = df_articles["text"].progress_apply(self._classify_text)

        # This line of code groups the DataFrame df_articles by two columns, 'date' and 'category', 
        # and then size() calculates the number of occurrences of each combination of the 'date' and 'category' columns
        # The reset_index method is used to reset the index of the resulting DataFrame to a new default index (start: 0), 
        # The argument name='count' specifies the name to be used for the new column holding the count values.
        df_grouped_by = df_articles.groupby(["date", "category"]).size().reset_index(name="count")

        # setting "date" as the new index
        df_per_date_index = df_grouped_by.set_index("date")
        #df_top_categories = (df_per_date_index.groupby("date").apply(lambda x: x.nlargest(5, "count", keep="all")).reset_index(level=0, drop=True)) # getting top 5
        df_output = df_per_date_index.sort_values(by=["date", "count"], ascending=[True, False])
                
        return df_output # returns the sorted DF
    

    def get_kws_by_date(self, kw_1: str, kw_2: str = "") -> pd.DataFrame:
        """Counts articles per category and date (scrape-date)"""

        keyword_1 = kw_1
        keyword_2 = kw_2

        # only run 1 keyword search if no 2nd keyword is given
        if keyword_2 == "":
            search_for_2_kws = False
        else:
            search_for_2_kws = True

        # make a working copy of the articles dataframe, leaving out the url column.
        df_kws_per_date = self.df_articles[["date", "text"]]

        # setting up the keyword count columns and the actual count (defdict)
        df_kws_per_date[keyword_1] = 0
        kw_1_count = defaultdict(int)

        if search_for_2_kws:
            df_kws_per_date[keyword_2] = 0
            kw_2_count = defaultdict(int)

        total_articles = len(self.df_articles["text"])

        if search_for_2_kws == False:

            for i, article in tqdm(enumerate(self.df_articles["text"]), total=total_articles, bar_format=self.custom_bar, ascii=" =", leave=False):

                # run _count_occurences on the article text, getting the amount of keyword occurences
                kw_1_count = self._count_occurences(article, kw_1) 

                # saving the amount to the proper column and row(i) in the DataFrame
                df_kws_per_date.loc[i, keyword_1] = kw_1_count["kw_count"]
        
        else:

            for i, article in tqdm(enumerate(self.df_articles["text"]), total=total_articles, bar_format=self.custom_bar, ascii=" =", leave=False):

                # run _count_occurences on the article text, getting the amount of keyword occurences
                kw_1_count = self._count_occurences(article, kw_1) 
                kw_2_count = self._count_occurences(article, kw_2)

                # saving the amount to the proper column and row(i) in the DataFrame
                df_kws_per_date.loc[i, keyword_1] = kw_1_count["kw_count"]
                df_kws_per_date.loc[i, keyword_2] = kw_2_count["kw_count"]

        # dropping the article text column
        df_kws_per_date = df_kws_per_date.drop("text", axis=1)

        # setting "date" as the new index
        df_kws_per_date = df_kws_per_date.set_index("date")

        # grouping on "date" and summarizing keyword_1 & keyword_2 columns individually
        df_kws_per_date = df_kws_per_date.groupby("date").sum()

        # sorting by date, oldest date at the top
        df_output = df_kws_per_date.sort_values(by="date", ascending=True)
                
        return df_output
    

    def get_cats_by_domain(self) -> pd.DataFrame:
        """Counts articles per category and group by domain."""

        # Calculate the total number of articles for tqdm's total parameter
        total_articles = len(self.df_articles)
      
        categorized_articles = defaultdict(lambda: defaultdict(int))
        for url, article in tqdm(zip(self.df_articles["url"], self.df_articles["text"]), total=total_articles, bar_format=self.custom_bar, ascii=" =", leave=False):
            main_category = self._classify_text(article)
            domain = re.sub(r"^https://(www.)?|/.*", "", url)
            categorized_articles[domain][main_category] += 1

        # Create a list of dictionaries representing each row of the output DataFrame
        output_rows = []
        for domain, categories in categorized_articles.items():
            for category, count in categories.items():
                output_rows.append({"domain": domain, "category": category, "count": count})
        
        # Create the output DataFrame and sort by "domain" and "count"
        df_output = pd.DataFrame(output_rows)
        df_output = df_output.sort_values(by=["domain", "count"], ascending=[True, False])
        #df_output = df_output.reset_index(level=0, drop=True)

        # setting "domain" as the new index
        df_output = df_output.set_index("domain")
        
        return df_output
    

    def get_country_mentions(self) -> pd.DataFrame:
        """Counts country mentions in all articles, using 2 different methods for single country names and multiple country names, for optimal speed."""

        # Dataframe of all country names + iso3 codes
        df_countries = pd.DataFrame(self.countries, columns=["country", "iso3_country_code"])

        ## Countries with multiple names - counting hits in all articles
        # Countries (iso3) with multiple names - counting mentions in all articles.
        country_multi_count = defaultdict(int)
        for article in tqdm(self.df_articles["text"], bar_format=self.custom_bar, ascii=" =", leave=False):
            for country, iso3 in self.countries_multi:
                pattern = fr"\b{country}\b"
                country_multi_count[iso3] += len(re.findall(pattern, article))
        df_iso3_multi = pd.DataFrame(country_multi_count.items(), columns=["iso3_country_code", "count"])

        # Creating a DataFrame for countries and iso3 with multiple names
        df_countries_multi = pd.DataFrame(self.countries_multi, columns=["country", "iso3_country_code"])

        # Merging the iso3 + counts and the country names/iso3
        df_countries_multi = df_countries_multi.merge(df_iso3_multi, left_on="iso3_country_code", right_on="iso3_country_code")

        ## Countries with single names - counting hits in all articles
        # Counting unique words in all articles.
        words_count = defaultdict(int)
        for word in tqdm(self.articles_words_list, bar_format=self.custom_bar, ascii=" =", leave=False):
            words_count[word] += 1
        df_all_articles_words_count = pd.DataFrame(words_count.items(), columns=["word", "count"])

        # By merging the single country names DF with the article words counts, we get the actual DF that has the mentions for countries with single names
        df_singles_result = df_countries.merge(df_all_articles_words_count, left_on="country", right_on="word")
        del df_singles_result["word"]

        ## Finalize data
        # Adding together both DFs for both countries with single and multiple names
        df_output = pd.concat([df_singles_result, df_countries_multi])

        # changing the USA + UK names to united states + united kingdom for easier summarizing
        df_output["country"] = df_output["country"].replace({"usa": "united states"})
        df_output["country"] = df_output["country"].replace({"america": "united states"})
        df_output["country"] = df_output["country"].replace({"uk": "united kingdom"})
        df_output["country"] = df_output["country"].replace({"england": "united kingdom"})

        df_output = df_output.groupby(['country', 'iso3_country_code'])['count'].sum().reset_index() # summarize all counts (especially for USA/UK which have several)
        df_output = df_output.sort_values(by=["count"], ascending=False)  # Sort DataFrame by "count"
        df_output = df_output.reset_index(level=0, drop=True)
       
        return df_output
    

    def get_detailed_statistics(self):

        # Dictionary to hold the results
        result = {}
        
        # Total Number of Scraped Articles
        total_articles = len(self.df_articles)
        result['total_articles'] = total_articles
        
        # Number of Actual Scraping Days
        unique_scrape_days = len(set(sql.execute(self.db, "SELECT DISTINCT scrape_date FROM articles;")))
        result['unique_scrape_days'] = unique_scrape_days
        
        # Scraping Time Period
        time_period_data = sql.execute(self.db, "SELECT MIN(scrape_date), MAX(scrape_date) FROM articles;")
        min_date, max_date = time_period_data[0]
        result['time_period'] = {'from_date': min_date, 'to_date': max_date}
        
        # Articles per Domain
        articles_per_domain = defaultdict(int)
        for url in self.df_articles["url"]:
            domain = re.search(r'https?://([A-Za-z_0-9.-]+).*', url).group(1)
            articles_per_domain[domain] += 1
        result['articles_per_domain'] = articles_per_domain

        return result