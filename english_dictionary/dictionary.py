import sqlite3

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
        return res

    def get_word_def(self, word: str):
        res = self.con.execute("SELECT definition FROM entries WHERE word=?", (word,)).fetchone()[0]
        return res

    def select_random_word(self):
        res = self.con.execute("SELECT * FROM entries GROUP BY RANDOM() LIMIT 1").fetchone()[0] # seems expensive but whatever
        return res