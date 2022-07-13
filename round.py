import json
import random

from numpy import False_, number
from timer import Timer
from english_dictionary.dictionary import Dictionary
from image_fetcher import ImageFetcher

GAMEVARS_PATH = "./gamevars.json"
with open(GAMEVARS_PATH, "r") as f:
    GAMEVARS = json.load(f)

class Round:
    def __init__(self, msg_pool, p1, p2, last_round=False, hint_lock=None):
        self.msg_pool = msg_pool
        self.p1 = p1
        self.p2 = p2
        self.last_round = last_round

        # private data, should not be accessible to the Guesser.
        self.__chosen_word = None
        self.__hints = None

        # variables for score calc, does not need to be shared.
        self.wrong_guess_count : int = None
        self.hints_count = None

        # public data, any changes made to then should be notified to both players.
        self.ex = None
        self.gsr = None
        self.board : list = None
        self.cguesses : set  = None
        self.fguesses : set = None
        self.hints : list = None
        self.hint_requested : bool = None
        self.p1scoreboard : dict = None
        self.p2scoreboard : dict = None
        self.rotated : bool = None
        self.round_state : int = None
        self.word_was_random : bool = None
        self.guessed_correctly : bool = None
        self.wrong_guesses : list = None

        # other
        self.current_timer = None
        self.hint_timer = Timer(GAMEVARS["TIME_FOR_CHOOSING_HINT"], round=self)
        self.stopped_prematurely = False
        self.hint_lock = hint_lock

    def handle_ready_stage(self):
        timer = Timer(GAMEVARS["TIME_FOR_READY"], send_updates=True, round=self)
        timer.start()
        timer.join()

    def handle_choose_word_stage(self):
        def finish_condition_check():
            return self.__chosen_word is not None
        def callback(): # callback is only called when the timer runs out.
            self.handle_player_actions(self.ex, msg={
                "msg_type": "action",
                "action_type": "choose_word",
                "content": "__RANDOM__",
            })
        timer = Timer(GAMEVARS["TIME_FOR_CHOOSING"], finish_condition_check=finish_condition_check, callback=callback, send_updates=True, round=self)
        self.current_timer = timer
        timer.start()
        timer.join()

    def handle_guess_word_stage(self):
        def finish_condition_check():
            if self.__chosen_word is None:
                return False
            if self.guessed_correctly or self.cguesses == set(self.__chosen_word):
                self.msg_pool.push(self.gsr, {"msg_type": "update", "update_type": "__chosen_word", "content": self.__chosen_word})
                self.finalize_score()
                return True
        def callback():
            self.msg_pool.push(self.gsr, {"msg_type": "update", "update_type": "__chosen_word", "content": self.__chosen_word})
            self.finalize_score()
        timer = Timer(GAMEVARS["TIME_FOR_GUESSING"], finish_condition_check=finish_condition_check, callback=callback, send_updates=True, round=self)
        self.current_timer = timer
        timer.start()
        timer.join()

    def handle_round_recess(self):
        timer = Timer(GAMEVARS["TIME_FOR_RECESS"], send_updates=True, round=self)
        self.current_timer = timer
        timer.start()
        timer.join()
        self.update_private_data("__chosen_word", None)
        self.update_private_data("__hints", {})

    def create_hints(self):
        with self.hint_lock:
            d = Dictionary()
            image_generator = ImageFetcher()
            if self.__chosen_word == None: return
            number_of_relevant_words = 2
            number_of_pics = 2
            hints =  {}
            word_types = d.get_word_types(self.__chosen_word)
            relevant_words = d.get_relevant_words(self.__chosen_word, number_of_relevant_words)
            pics = image_generator.get_url_from_keyword(self.__chosen_word, number_of_pics)
            count = 1
            hints[count] = {"id": count, "hint_type": "word_types", "content": word_types}
            count += 1
            for i in relevant_words:
                hints[count] = ({"id": count, "hint_type": "relevant_words", "content": i})
                count += 1
            for i in pics:
                hints[count] = ({"id": count, "hint_type": "image", "content": i})
                count += 1
            self.update_private_data("__hints", hints)
            # print(self.__hints)
    
    def update_public_data(self, var_name: str, new_data):
        def get_serializable(new_data):
            if new_data is self.p1 or new_data is self.p2:
                return new_data.id
            elif type(new_data) == set:
                return list(new_data)
            return new_data
        def update_ex(data):
            self.ex = data
        def update_gsr(data):
            self.gsr = data
        def update_board(data):
            self.board = data
        def update_cguesses(data):
            self.cguesses = data
        def update_fguesses(data):
            self.fguesses = data
        def update_hints(data):
            self.hints = data
        def update_hint_requested(data):
            self.hint_requested = data
        def update_p1scoreboard(data):
            self.p1scoreboard = data
        def update_p2scoreboard(data):
            self.p2scoreboard = data
        def update_rotated(data):
            self.rotated = data
        def update_round_state(data):
            self.round_state = data
        def update_word_was_random(data):
            self.word_was_random = data
        def update_guessed_correctly(data):
            self.guessed_correctly = data
        def update_wrong_guesses(data):
            self.wrong_guesses = data
        mapping = {
            "ex": update_ex,
            "gsr": update_gsr,
            "board": update_board,
            "cguesses": update_cguesses,
            "fguesses": update_fguesses,
            "hints": update_hints,
            "hint_requested": update_hint_requested,
            "p1scoreboard": update_p1scoreboard,
            "p2scoreboard": update_p2scoreboard,
            "rotated": update_rotated,
            "round_state": update_round_state,
            "word_was_random": update_word_was_random,
            "guessed_correctly": update_guessed_correctly,
            "wrong_guesses": update_wrong_guesses
        }
        mapping[var_name](new_data)
        msg = {
            "msg_type": "update",
            "update_type": var_name,
            "content": get_serializable(new_data)
        }
        self.msg_pool.push(self.p1, msg)
        self.msg_pool.push(self.p2, msg)
    
    def update_private_data(self, var_name, new_data):
        if var_name == "__chosen_word":
            self.__chosen_word = new_data
            if self.__chosen_word is None:
                msg = {
                    "msg_type": "update",
                    "update_type": "__chosen_word",
                    "content": None
                }
                self.msg_pool.push(self.p1, msg)
                self.msg_pool.push(self.p2, msg)
            else:
                self.msg_pool.push(self.ex, {"msg_type": "update", "update_type": "__chosen_word", "content": self.__chosen_word})
        elif var_name == "__hints":
            self.__hints = new_data
            if self.__hints is None or len(self.__hints) == 0:
                msg = {
                    "msg_type": "update",
                    "update_type": "__hints",
                    "content": []
                }
                self.msg_pool.push(self.p1, msg)
                self.msg_pool.push(self.p2, msg)
            else:
                self.msg_pool.push(self.ex, {"msg_type": "update", "update_type": "__hints", "content": list(self.__hints.values())})
        elif var_name == "wrong_guess_count":
            self.wrong_guess_count = new_data

    def finalize_score(self):
        guesser = self.gsr
        disconnected = self.p1scoreboard["DISCONNECTED"] if guesser == self.p1 else self.p2scoreboard["DISCONNECTED"]
        total_score = 0
        if guesser is self.p1:
            total_score = self.p1scoreboard["GAME_TOTAL"]
        else:
            total_score = self.p2scoreboard["GAME_TOTAL"]
        word_was_guessed = self.guessed_correctly or set(self.__chosen_word) == set(self.cguesses)
        number_of_letters_in_word = len(set(self.__chosen_word))
        number_of_correct_guesses = len(self.cguesses)
        number_of_false_guesses = len(self.fguesses)
        res = {
            "ID": self.gsr.id,
            "FINISHED_GUESSING": True,
            "PROGRESSION": 0,
            "BASE": 0,
            "BONUS": 0,
            "PENALTY": 0,
            "COMPENSATION": 0,
            "ROUND_TOTAL": 0,
            "GAME_TOTAL": 0,
            "DISCONNECTED": disconnected,
        }
        # PROGRESSION SCORE CALCULATION
        prog_points = GAMEVARS["MAX_PROGRESSION_POINTS"] if word_was_guessed else GAMEVARS["MAX_PROGRESSION_POINTS"] * (number_of_correct_guesses / number_of_letters_in_word)
        res["PROGRESSION"] = int(prog_points)
        # BASE SCORE CALCULATION
        base_points = 0 if not word_was_guessed else GAMEVARS["MAX_BASE_POINTS"] * ( (26 - number_of_false_guesses - number_of_correct_guesses) / (26 - number_of_correct_guesses) )
        res["BASE"] = int(base_points)
        # BONUS SCORE CALCULATION
        if not word_was_guessed or set(self.__chosen_word) == set(self.cguesses):
            res["BONUS"] = 0
        else:
            res["BONUS"] = int(GAMEVARS["MAX_BONUS_POINTS"] * ((number_of_letters_in_word - number_of_correct_guesses) / number_of_letters_in_word))
        # PENALTY CALCULATION
        res["PENALTY"] = int(GAMEVARS["PENALTY_FOR_HINT"] * self.hints_count + GAMEVARS["PENALTY_FOR_FALSE_GUESS"] * self.wrong_guess_count)
        # COMPENSATION CALCULATION
        res["COMPENSATION"] = int(GAMEVARS["COMPENSATION_FOR_RANDOM"] if self.word_was_random else 0)
        res["ROUND_TOTAL"] = int(res["PROGRESSION"] + res["BASE"] + res["BONUS"] + res["PENALTY"] + res["COMPENSATION"])
        res["GAME_TOTAL"] = int(res["ROUND_TOTAL"] + total_score) if not disconnected else 0
        self.update_public_data("p1scoreboard" if self.gsr is self.p1 else "p2scoreboard", res)
    
    def player_choose_word(self, content : str) -> tuple:
        def get_board():
            return [c if c in self.cguesses else "_" for c in self.__chosen_word]

        d = Dictionary()
        if content == "__RANDOM__":
            self.update_public_data("word_was_random", True)
            while not content.isalpha():
                content = d.select_random_word()
        else:
            if len(content) <= 2:
                return (True, "warning", "Word must be longer than 2 characters. Please choose again.")
            elif not content.isalpha():
                return (True, "warning", "Word contains invalid character(s). Please choose again.")
            elif not d.check_if_word_exists(content):
                return (True, "warning", "Word does not exist in our dictionary. Please choose again.")
        word = content.upper()
        self.update_private_data("__chosen_word", word)
        self.update_public_data("board", get_board())
        return (True, "success", "Valid word choice!")

    def player_change_word(self, content : str) -> tuple:
        d = Dictionary()
        new_word = content.upper()
        def get_word_signature(word):
            return "".join([c if c in self.cguesses else "_" for c in word])

        if not get_word_signature(new_word) == get_word_signature(self.__chosen_word):
            return (True, "warning", "NOT ACCEPTED. Word choice does not fit with current progress.")
        elif not d.check_if_word_exists(new_word):
            return (True, "warning", "NOT ACCEPTED. Word does not exist in our dictionary.")
        elif len(set(new_word).intersection(self.fguesses)) != 0:
            return (True, "warning", "NOT ACCEPTED. Word choice contains an already falsely guessed letter.")
        elif new_word == self.__chosen_word:
            return (True, "warning", "NOT ACCEPTED. Cannot change to current word.")
        elif new_word in self.wrong_guesses:
            return (True, "warning", "NOT ACCEPTED. This word has already been guessed by the Guesser.")
        else:
            overtime = GAMEVARS["OVERTIME_FOR_CHANGE"]
            msg = {
                "msg_type": "notification",
                "show": True,
                "notification_type": "warning",
                "content": f"The Executioner has changed the word. Game time extended by {overtime} seconds.",
                "tag": "WORD_UPDATED"
            }
            # reset hints
            self.update_public_data("hints", [])
            self.hints_count = 0
            self.update_private_data("__chosen_word", new_word)
            self.update_private_data("__hints", {})
            self.update_private_data("__hints", None)
            self.msg_pool.push(self.gsr, msg)
            self.current_timer.extend(overtime)
            return (True, "success", "Word changed successfully!")

    def player_choose_hint(self, content):
        if self.__hints is None: return
        if content not in self.__hints and content != "__RANDOM__":
            return (True, "warning", "Not a valid hint choice.")
        else:
            if content == "__RANDOM__":
                content = random.choice(list(self.__hints))
            self.hints.append(self.__hints[content])
            self.update_public_data("hints", self.hints)
            self.update_public_data("hint_requested", False)
            del self.__hints[content]
            self.update_private_data("__hints", self.__hints)
            notif = {
                "msg_type": "notification",
                "show": True,
                "notification_type": "success",
                "content": "New hint has been added to the list. Scroll to view the new hint.",
                "tag": "HINT_UPDATED"
            }
            self.msg_pool.push(self.p1, notif)
            self.msg_pool.push(self.p2, notif)
            return (True, "success", "Valid hint choice.")

    def player_guess_letter(self, content):
        def get_board():
            return [c if c in self.cguesses else "_" for c in self.__chosen_word]

        letter = content.upper()
        if letter in self.cguesses or letter in self.fguesses: return (False, "warning", "Invalid request.")
        else:
            if letter in self.__chosen_word:
                self.cguesses.add(letter)
                self.update_public_data("cguesses", self.cguesses)
                self.update_public_data("board", get_board())
            else:
                self.fguesses.add(letter)
                self.update_public_data("fguesses", self.fguesses)
            return (False, "success", "Choice was valid.")

    def player_guess_word(self, content):
        word = content.upper()
        if word == self.__chosen_word: 
            self.update_public_data("guessed_correctly", True)
            return (True, "success", "Your guess was correct!")
        else: 
            self.update_private_data("wrong_guess_count", self.wrong_guess_count + 1)
            self.wrong_guesses.append(word)
            self.update_public_data("wrong_guesses", self.wrong_guesses)
            return (True, "warning", "Your guess was incorrect. Said amount of points deducted.")

    def player_request_hint(self, content):
        def finish_condition_check():
            if len(self.hints) == self.hints_count:
                self.hint_timer = Timer(GAMEVARS["TIME_FOR_CHOOSING_HINT"], round=self)
                return True
            return False
        def callback():
            # choose for the player.
            self.handle_player_actions(self.ex, msg={
                "msg_type": "action",
                "action_type": "choose_hint",
                "content": "__RANDOM__",
            })
            self.update_public_data("hint_requested", False)
            self.hint_timer = Timer(GAMEVARS["TIME_FOR_CHOOSING_HINT"], round=self)
        if self.hint_timer.is_alive(): 
            return (False, "warning", "Cannot request hint at this moment.")
        elif self.__hints is not None and len(self.__hints) == 0:
            return (False, "warning", "Cannot request more hints.")
        else:
            if self.__hints is None:
                self.create_hints()
            self.hints_count += 1
            self.hint_timer.finish_condition_check = finish_condition_check
            self.hint_timer.callback = callback
            self.hint_timer.start()
            self.update_public_data("hint_requested", True)
            return (True, "success", "Please wait for the Executioner to choose a hint...")

    def handle_player_actions(self, player, msg):
        action_type = msg["action_type"]
        content = msg["content"]
        function_mapping = {
            "choose_word": self.player_choose_word,
            "change_word": self.player_change_word,
            "choose_hint": self.player_choose_hint,
            "guess_letter": self.player_guess_letter,
            "guess_word": self.player_guess_word,
            "request_hint": self.player_request_hint
        }
        response = function_mapping[action_type](content)
        if response is not None:
            self.msg_pool.push(
                player, {
                    "msg_type": "notification", 
                    "show": response[0],
                    "notification_type": response[1], 
                    "content": response[2],
                    "tag": None
                    }
                )
    
    
    def start_round(self, p1gt=0, p2gt=0):

        # set initial data for first half round.
        self.__hints = None
        self.wrong_guess_count = 0
        self.hints_count = 0
        self.update_public_data("ex", self.p1)
        self.update_public_data("gsr", self.p2)
        self.update_public_data("board", [])
        self.update_public_data("cguesses", set())
        self.update_public_data("fguesses", set())
        self.update_public_data("hints", [])
        self.update_public_data("hint_requested", False)
        self.update_public_data("p1scoreboard", {"ID": self.p1.id, "FINISHED_GUESSING": False, "GAME_TOTAL" : p1gt, "DISCONNECTED" : False})
        self.update_public_data("p2scoreboard", {"ID": self.p2.id, "FINISHED_GUESSING": False, "GAME_TOTAL" : p2gt, "DISCONNECTED" : False})
        self.update_public_data("rotated", False)
        self.update_public_data("word_was_random", False)
        self.update_public_data("guessed_correctly", False)
        self.update_public_data("wrong_guesses", [])

        # handle pacing of first half round.
        self.update_public_data("round_state", GAMEVARS["ROUND_STATE_READY"])
        self.handle_ready_stage()
        self.update_public_data("round_state", GAMEVARS["ROUND_STATE_CHOOSING_WORD"])
        self.handle_choose_word_stage()
        self.update_public_data("round_state", GAMEVARS["ROUND_STATE_GUESSING_WORD"])
        self.handle_guess_word_stage()
        self.update_public_data("round_state", GAMEVARS["ROUND_STATE_RECESS"])
        self.handle_round_recess()

        # set initial data for second half round.
        self.__hints = None
        self.wrong_guess_count = 0
        self.hints_count = 0
        self.update_public_data("ex", self.p2)
        self.update_public_data("gsr", self.p1)
        self.update_public_data("board", [])
        self.update_public_data("cguesses", set())
        self.update_public_data("fguesses", set())
        self.update_public_data("hints", [])
        self.update_public_data("hint_requested", False)
        self.update_public_data("p1scoreboard", self.p1scoreboard)
        self.update_public_data("p2scoreboard", self.p2scoreboard)
        self.update_public_data("rotated", True)
        self.update_public_data("word_was_random", False)
        self.update_public_data("guessed_correctly", False)
        self.update_public_data("wrong_guesses", [])

        # handle pacing of second half round.
        self.update_public_data("round_state", GAMEVARS["ROUND_STATE_READY"])
        self.handle_ready_stage()
        self.update_public_data("round_state", GAMEVARS["ROUND_STATE_CHOOSING_WORD"])
        self.handle_choose_word_stage()
        self.update_public_data("round_state", GAMEVARS["ROUND_STATE_GUESSING_WORD"])
        self.handle_guess_word_stage()
        self.update_public_data("round_state", GAMEVARS["ROUND_STATE_RECESS"])
        self.handle_round_recess()

        return (self.p1scoreboard["GAME_TOTAL"], self.p2scoreboard["GAME_TOTAL"])