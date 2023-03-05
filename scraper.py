# Standard modules
import re
import random as rd
import time
import logging

# Third-party modules -> requirements.txt
import requests
from bs4 import BeautifulSoup

# DEBUG
import data_init
from text_processor import TextProcessor


class WebScraper():  

    url_start = "https://www."

    def scrape_sleep(self):
        time.sleep(rd.randint(1,3)) # adding some delay on purpose in between requests so we minimize the chance of being banned by the site


    def TextScraper(self, headers: str, url: str, div_filter: str, p_attr_exclusion: list, sleep: bool, debug_mode: bool = False) -> str:

        scraped_text = ""

        if sleep:
            self.scrape_sleep() # sleep time delay to minimze getting banned by a site

        try:
            response = requests.get(url, headers=headers) # saving a request's "response" from the URL
            
        except requests.exceptions.ConnectionError as e:
            logging.error(f"URL: {url}\n\nInfo: {e}")
            raise

        print(f"Scraping URL: {url}") if debug_mode else None # DEBUG
        print(f"Status code: {response.status_code}") if debug_mode else None # DEBUG

        if response.status_code != 200: # the HTML "success" status response code is 200
            logging.info(f"{response.url}\n\nHTTP Status Code: {response.status_code}")
            raise requests.exceptions.ConnectionError
            
        soup = BeautifulSoup(response.text, "lxml")

        div = soup.find("div", class_=re.compile(div_filter))

        # if the soup comes back empty (meaning that the there's no such class name) it will go after the "id" attribute name
        if not div:
            div = soup.find("div", id=re.compile(div_filter))
      
        # raise ValueError if we didn't get any text at all
        if not div:
            logging.info(f"{response.url}\n\nInfo: Requested <div> was not found on this page.")
            raise ValueError("Requested <div> was not found on this page.")

        # raise ValueError if we didn't get any text at all
        if not div.text:
            logging.info(f"{response.url}\n\nInfo: The content of the requested <div> was empty.")
            raise ValueError("The content of the requested <div> was empty.")
      
        paragraphs = div.find_all("p")

        print(f"<p> paragraphs: {len(paragraphs)}") if debug_mode else None # DEBUG

        p_amount = len(paragraphs)

        # if it's less than 7 paragraph we count it as too short for saving, and try a backup which is going after all classes with "paragraph" inside the name
        if len(paragraphs) < 7:
            paragraphs = div.find_all(class_=re.compile("paragraph"))
            print(f"<class name> paragraphs: {len(paragraphs)}") if debug_mode else None # DEBUG

        # if no divs are found with our backup tactic we raise an error
        if not div:
            logging.info(f"{response.url}\n\nInfo: Requested <div> was not found on this page.")
            raise ValueError("Requested <div> was not found on this page.")
        
        # get the correct <p> amount for error logging
        if p_amount < len(paragraphs):
            p_amount = len(paragraphs)

        # if it's still not enough "content" we raise a Value Error
        if len(paragraphs) < 7:
            logging.info(f"{response.url}\n\nInfo: The content of the requested <div> was not worth saving (too few paragraphs: {p_amount}).")
            raise ValueError(f"The content of the requested <div> was not worth saving (too few paragraphs: {p_amount}).")
   
        paragraphs_clean = []

        # check for exclusion tags
        exclude_check = div.find(class_=re.compile("exclude"))

        for p in paragraphs:

            if p.parent.name == "figcaption": # continue to the next paragraph if this one is inside a "Figure Caption" element. We don't want pic info text.
                continue

            # remove <p> tags that have child classes with unwanted content
            if exclude_check:
                if p.find(class_=re.compile("exclude")):
                    continue

            p_attrs_list = list(p.attrs.values()) # make a more accessable list out of the dict view object (which contains the <p> attributes)
            # an example of how this could look: [['promo-category'], 'category']
            
            print(p_attrs_list) if debug_mode else None # use this for debugging to see paragraphs that shouldn't be included in the final saved article text # DEBUG

            #  the order             1           4            5              2          3
            sublists_flattened = [element for sublist in p_attrs_list for element in sublist if type(sublist) is list] # extracting the words in the inner lists
            list_flattened = [element for element in p_attrs_list if type(element) is str] # extracting the words in the list
            final_p_attrs_list = sublists_flattened + list_flattened # putting these 2 lists together for easier keyword comparison

            # check if any paragraph contains any of the excluded keywords , if so: don't save that paragraph to the final article text
            # the any()-method returns True whenever a particular element is present in a given iterator
            check = any(keyword in word for word in final_p_attrs_list for keyword in p_attr_exclusion)
            
            if check: # continue to the next paragraph iteration and don't save this one which contains an unwanted tag
                continue

            paragraphs_clean.append(p)

        scraped_text = ' '.join([paragraph.get_text().strip() for paragraph in paragraphs_clean]) # converting the list of words into a single string

        return scraped_text


    def URLScraper(self, headers: str, url_domain: str, url_pages: list, url_filter: str, url_exclusion: list, pagin_filter: str, pagin_amount: int = 1, debug_mode: bool = False) -> list:

        final_url_article_links = []


        for page in url_pages:

            url_pagin = ""

            for i in range(1, pagin_amount + 1):

                print(f"--- Pgn level: {i} ---") if debug_mode else None # DEBUG

                if page != "/":
                    url_page = f"{url_domain}{page}"
                else:
                    url_page = f"{url_domain}"

                url_article_links = []

                print(f"URL: {self.url_start}{url_page}") if debug_mode else None # DEBUG
                
                self.scrape_sleep() # sleep time delay to minimze getting banned by a site

                try:
                    response = requests.get(self.url_start + url_page + url_pagin, headers=headers) # saving a request's "response" from the URL
                    
                except requests.exceptions.ConnectionError as e:
                    logging.error(f"URL: {self.url_start}{url_page}{url_pagin}\n\nError info: {e}")
                    raise

                print(f"Resp URL: {response.url}") if debug_mode else None # DEBUG
                print(f"Status code: {response.status_code}") if debug_mode else None # DEBUG
                
                if response.status_code != 200: # the HTML "success" status response code is 200
                    logging.info(f"URL: {response.url}\n\nHTTP Status Code: {response.status_code}")
                    raise requests.exceptions.ConnectionError
                        
                soup = BeautifulSoup(response.text, "lxml")
                all_hrefs = soup.find_all(href=True) # don't use "a" specifically, since some sites put the href's inside other tags like <h3> for example
                url_article_links = [link["href"] for link in all_hrefs if re.search(url_filter, link["href"])] # getting the actual article urls
                url_article_links = list(set(url_article_links)) # getting rid of possible duplicates thanks to python's "set" data structure


                ## Pagination

                # 1st check - <a> tag that contains the keyword (wildcard thanks to re.compile)
                if pagin_filter:
                    pagination = soup.find_all("a", re.compile(pagin_filter))
                    if pagination:
                        print("1st pagination level - <a> re.compile name") if debug_mode else None # DEBUG

                        # we want the more/next pagination button so we're going to check for "next" or "more" in the tag attributes
                        for tag in pagination:

                            tag_attrs = list(tag.attrs.values())

                            sublists_flattened = [element for sublist in tag_attrs for element in sublist if type(sublist) is list] # extracting the words in the inner lists
                            list_flattened = [element for element in tag_attrs if type(element) is str] # extracting the words in the list
                            final_tag_attrs_list = sublists_flattened + list_flattened # putting these 2 lists together for easier keyword comparison

                            check_next = any("next" in word for word in final_tag_attrs_list)
                            check_more = any("more" in word for word in final_tag_attrs_list)

                            if check_next or check_more:
                                url_pagin = tag["href"]   


                    # 2nd check: "aria-label" inside an "a" tag
                    if not pagination:
                        pagination = soup.find_all("a", attrs={"aria-label": pagin_filter}) # get the tag pagination info
                        if pagination:
                            print("2nd pagination level - <a> aria-label") if debug_mode else None # DEBUG
                            url_pagin = pagination[0]["href"]
                    
                    # 3rd check - class name and "?" inside it's href
                    if not pagination:
                        pagination = soup.find(class_=pagin_filter) # get the tag pagination info
                        if pagination:
                            pagination = list(pagination.attrs.values()) # get the url for the next page
                            pagination = [element for element in pagination if type(element) is str if "?" in element] # if there is a "?" in the url
                            if pagination:
                                print("3rd pagination level - class name") if debug_mode else None # DEBUG
                                url_pagin = pagination[0] # [0] extracting the pagination link

                    print(f"Before pagin url modification: {url_pagin}") if debug_mode else None # DEBUG
                
                ## Modify the pagination link to be able to connect the relative ending to our root domain
                # we use regular expressions for these tasks. 
                # for example: '^.*\?' matches any sequence of characters (.*) that occurs at the beginning of the string (^) and ends with a question mark (\?).
                if url_pagin:
                    url_pagin = re.sub(r"^.*\?", "?", url_pagin) # remove all characters before "?"

                    url_pagin = re.sub(r"^.*" + url_page, "", url_pagin) # get the relative pagination link if a full url was scraped
                    
                    print(f"Before relative root creation: {url_pagin}") if debug_mode else None # DEBUG
                    relative_root = re.sub(r"^.*/", "/", url_page) # get the correct "relative root" extension if the original url has more than just the domain with prefix in the end
                    print(f"Relative root: {relative_root}") if debug_mode else None # DEBUG

                    url_pagin = re.sub(relative_root, "", url_pagin) # subtract the original extension from the scraped url to get one we can use with the initial url

                print("Pgn URL for 'Next page': " + url_pagin) if debug_mode else None # DEBUG
                print() if debug_mode else None # DEBUG


                # some sites have the relative url to the individual sub urls. This makes sure so that the whole correct url gets saved.
                # some urls have "www." in them. That gets stripped away
                # these if-statements's also work as a filter not to include random urls to external sites, social pages, emails or unwanted urls on the same site
                
                for link in url_article_links:

                    if any(re.search(regex, link) for regex in url_exclusion): # unwanted sub urls
                        continue

                    if re.match(r"^.*://" + re.escape(url_page) + r"/?$", link): # if it somehow scraped the url to the main page
                        continue
                    
                    if re.sub(r"^https://(www.)?|/.*", "", link) != url_domain: # if it scraped articles from to other domains (domain: .com, scraped: .co.uk)
                        continue

                    # remove ? and everything after, example "?utm_source=homepage&utm_medium=TopNews"
                    link = re.sub(r"\?.*", "", link)

                    # clean the link depending on different situations
                    if link.startswith("/"): # relative url (relative to the domain)
                        final_url_article_links.append("https://" + url_domain + link)

                    elif link.startswith(self.url_start): # removing "www." from the url if it's present, so all saved urls will have the same format
                        final_url_article_links.append(re.sub("www.", "", link))

                    elif link.startswith("https://" + url_domain): # standard url
                        final_url_article_links.append(link)


                # prevent the pagination looping on this page if no pagination is found
                if url_pagin == "":
                    break

        final_url_article_links = list(set(final_url_article_links)) # getting rid of possible duplicates thanks to python's "set" data structure

        return final_url_article_links