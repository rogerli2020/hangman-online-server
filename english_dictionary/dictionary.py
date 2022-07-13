import sqlite3
from random import shuffle
import re

# database schema: entries(word, wordtype, definition)
DIC_PATH = "english_dictionary/English-Dictionary-Database/Dictionary.db"

class Dictionary:
    def __init__(self) -> None:
        self.con = sqlite3.connect(DIC_PATH)
        self.cur = self.con.cursor()
    
    def check_if_word_exists(self, word: str) -> bool:
        res = self.con.execute("""
            SELECT COUNT(*)
            FROM entries
            WHERE word=?
        """, (word, )).fetchone()[0]
        
        return True if res >= 1 else False

    def get_word_types(self, word: str) -> list:
        res = self.con.execute("SELECT wordtype FROM entries WHERE word=?", (word,)).fetchall()
        for i in range(len(res)): res[i] = res[i][0]
        return list(set(res))

    def get_word_def(self, word: str):
        res = self.con.execute("SELECT definition FROM entries WHERE word=?", (word,)).fetchone()[0]
        return res

    def select_random_word(self):
        res = self.con.execute("SELECT * FROM entries GROUP BY RANDOM() LIMIT 1").fetchone()[0] # seems expensive but whatever
        return res

    def select_relevant_words(self, word):
        word = word.upper()
        word_def = self.get_word_def(word).upper()
        word_def_list = word_def.split(" ")
        for i in range(0, len(word_def_list)):
            word_def_list[i] = re.sub(r'\W+', '', word_def_list[i])
        unhelpful_words = (
            'A', 
            'AN', 
            'OF', 
            'THE', 
            'OR', 
            'AND', 
            'ABOUT', 
            'AS', 
            'TO', 
            'WITH', 
            '', 
            'ESPECIALLY',
            'SUCH',
            'FROM',
            'NOT',
            'BY',
            'THAT',
            'IN',
            'IS',
            'ARE',
            'OFTEN',
            'USUALLY',
            'WHICH',
            'ITS',
            word
        )
        filtered = filter(lambda word: word not in unhelpful_words, word_def_list)
        filtered = list(set(filtered))
        return filtered
    
    def get_relevant_words(self, word, count):
        hints = []
        relevants = self.select_relevant_words(word)
        shuffle(relevants)

        for _ in range(0, count):
            if len(relevants) == 0:
                break
            curr = relevants.pop()
            hints.append(curr)
        
        return hints