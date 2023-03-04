from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation as punc
import re


class TextProcessor():

    stop_words = STOP_WORDS
    punc = re.sub(r"'|-|@", "", punc) # removing some symbols to later correctly filter out apostrophes/endings, emails and keep compound words
    punc += "—“”" # adding more special characters to the punctuations


    def text_cleaner(self, text: str) -> str:

        if type(text) is not str:
            raise TypeError(f"This function only accepts the type: 'string'. Instead you tried inserting a: '{type(text)}'")

        # remove punctuations from the text
        text = ''.join([char for char in text if char not in self.punc])

        # change all of the alphabetical characters in the text to lower case + split the text into single elements
        word_list = text.lower().split()

        # remove any links and emails in the text
        word_list = [word for word in word_list if "http" not in word]

        # remove apostrophes/incl endings after it
        for i, word in enumerate(word_list):
            for symbol in ["’", "'"]:
                if symbol in word:
                    word_list[i] = word.split(symbol)[0]

        # remove numerical values & punctuations/weird symbols
        word_list = [word for word in word_list if self.is_compound(word) or word.isalpha()]

        # remove stop words like "its", "an", "the", "for", "and", "that" and words with only 1 letter (post apostrophe chopping)
        word_list = [word for word in word_list if not word in self.stop_words and len(word) > 1]

        # convert the list back to a string
        article_text = " ".join(word_list)
        
        return article_text

    # check if a word is a hyphenated compound one, for example "stand-up"
    def is_compound(self, word: str) -> bool:
        if "-" in word[1:-1] and "-" not in [word[0], word[-1]]:
            word = word.split("-")
            for i in range(len(word)):
                if not word[i].isalpha():
                    return False
            return True


# DEBUG
# text = """test@email.com In interviews with Dallas’ 105.3 The Fan and the Dallas Morning News, Irvin said the conversation with the woman lasted between 45 seconds 
# and one minute. Irvin also said he initially didn’t remember the meeting because stand-up up-stand- -stand -up “I had a few drinks, to tell you the truth.”"""

# tp = TextProcessor()
# print(tp.text_cleaner(text))