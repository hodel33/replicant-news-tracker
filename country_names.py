from collections import defaultdict
import country_converter as coco
from country_list import countries_for_language as colang


class CountryNames():
    '''Returns a dict of all the countries with their names as keys, and nested dicts of iso2 + iso3 as key/value pairs inside'''

    def __init__(self):

        # importing the countries (english name)
        self.dict_countries = dict(colang('en'))

    def get_dict(self) -> dict:

        self.dict_inv = defaultdict(list)
        # inverting the key, value pairs. 
        # We want the actual country name as keys and a nested dict of iso2, iso3 values inside
        {self.dict_inv[v].append(k) for k, v in self.dict_countries.items()}

        dict_countries = defaultdict(lambda: defaultdict(dict))
        # adding the "iso2" key to the values that we had
        dict_countries = {k: {"iso2": v[0]} for k, v in self.dict_inv.items()}

        #print(dict_countries)

        # getting an "iso2"-list of all countries
        iso2_list = [v['iso2'] for v in dict_countries.values()]

        # get the "iso3" info from the "iso"-list
        iso3_list = coco.convert(names=iso2_list, to='ISO3', not_found='NULL')

        # assigning the "iso3"-values to the dict
        for i, country in enumerate(dict_countries):
            dict_countries[country]["iso3"] = iso3_list[i]

        # adding more variations for some country names
        dict_countries["America"] = dict_countries["United States"]
        dict_countries["USA"] = dict_countries["United States"]
        dict_countries["England"] = dict_countries["United Kingdom"]
        dict_countries["UK"] = dict_countries["United Kingdom"]

        return dict_countries
    
    def get_list(self) -> list:

        self.dict_inv = defaultdict(list)
        # inverting the key, value pairs. 
        # We want the actual country name as keys and a nested dict of iso2, iso3 values inside
        {self.dict_inv[v].append(k) for k, v in self.dict_countries.items()}

        dict_countries = defaultdict(lambda: defaultdict(dict))
        # adding the "iso2" key to the values that we had
        dict_countries = {k: {"iso2": v[0]} for k, v in self.dict_inv.items()}

        #print(dict_countries)

        # getting an "iso2"-list of all countries
        iso2_list = [v['iso2'] for v in dict_countries.values()]

        # get the "iso3" info from the "iso"-list
        iso3_list = coco.convert(names=iso2_list, to='ISO3', not_found='NULL')

        # assigning the "iso3"-values to the dict
        for i, country in enumerate(dict_countries):
            dict_countries[country]["iso3"] = iso3_list[i]

        # adding more variations for some country names
        dict_countries["America"] = dict_countries["United States"]
        dict_countries["USA"] = dict_countries["United States"]
        dict_countries["England"] = dict_countries["United Kingdom"]
        dict_countries["UK"] = dict_countries["United Kingdom"]

        # adding some countries that aren't in the imported libraries
        dict_countries["Macedonia"] = {'iso2': 'MK', 'iso3': 'MKD'}
        dict_countries["Somalia"] = {'iso2': 'SO', 'iso3': 'SOM'}
        dict_countries["Timor-Leste"] = {'iso2': 'TL', 'iso3': 'TLS'}

        return dict_countries


# DEBUG
if __name__ == "__main__":
    dict_countries = CountryNames().get_dict()
    print(dict_countries)