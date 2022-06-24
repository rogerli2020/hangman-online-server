import json
from timer import Timer
from english_dictionary.dictionary import Dictionary

GAMEVARS_PATH = "./gamevars.json"
with open(GAMEVARS_PATH, "r") as f:
    GAMEVARS = json.load(f)

class Round:
    def __init__(self, msg_pool, p1, p2, last_round=False):
        self.msg_pool = msg_pool
        self.p1 = p1
        self.p2 = p2
        self.last_round = last_round

        # private data, should not be accessible to the Guesser.
        self.__chosen_word = None
        self.__hints : dict = {1:1}

        # variables for score calc, does not need to be shared.
        self.wrong_guess_count : int = 0

        # public data, any changes made to then should be notified to both players.
        self.ex = self.p1
        self.gsr = self.p2
        self.board : list = []
        self.cguesses : set  = set()
        self.fguesses : set = set()
        self.hints : list = []
        self.hint_requested : bool = []
        self.p1scoreboard : dict = {"GAME_TOTAL" : 0}
        self.p2scoreboard : dict = {"GAME_TOTAL" : 0}
        self.rotated : bool = False
        self.round_state : int = False
        self.word_was_random : bool = False
        self.guessed_correctly : bool = False

        # other
        self.hint_timer = Timer(GAMEVARS["TIME_FOR_CHOOSING_HINT"])
        self.hints_count = 0

    def handle_ready_stage(self):
        timer = Timer(GAMEVARS["TIME_FOR_READY"])
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
        timer = Timer(GAMEVARS["TIME_FOR_CHOOSING"], finish_condition_check=finish_condition_check, callback=callback)
        timer.start()
        timer.join()

    def handle_guess_word_stage(self):
        def finish_condition_check():
            if self.__chosen_word is None:
                return False
            if self.guessed_correctly or self.cguesses == set(self.__chosen_word):
                self.finalize_score()
                return True
        def callback():
            self.finalize_score()
        timer = Timer(GAMEVARS["TIME_FOR_GUESSING"], finish_condition_check=finish_condition_check, callback=callback)
        timer.start()
        timer.join()

    def handle_round_recess(self):
        timer = Timer(GAMEVARS["TIME_FOR_RECESS"])
        timer.start()
        timer.join()

    def handle_hint_requested(self):
        def finish_condition_check():
            pass
        def callback():
            pass
        timer = Timer(GAMEVARS["TIME_FOR_CHOOSING_HINT"])
        timer.start()
    
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
            "guessed_correctly": update_guessed_correctly
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
        elif var_name == "__hints":
            self.__hints = new_data
        elif var_name == "wrong_guess_count":
            self.wrong_guess_count = new_data

    
    def finalize_score(self):
        guesser = self.gsr
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
            "PROGRESSION": 0,
            "BASE": 0,
            "BONUS": 0,
            "PENALTY": 0,
            "COMPENSATION": 0,
            "ROUND_TOTAL": 0,
            "GAME_TOTAL": 0
        }
        # PROGRESSION SCORE CALCULATION
        res["PROGRESSION"] = GAMEVARS["MAX_PROGRESSION_POINTS"] if word_was_guessed else GAMEVARS["MAX_PROGRESSION_POINTS"] * (number_of_correct_guesses / number_of_letters_in_word)
        # BASE SCORE CALCULATION
        res["BASE"] = 0 if not word_was_guessed else GAMEVARS["MAX_BASE_POINTS"] * ( (26 - number_of_false_guesses - number_of_correct_guesses) / (26 - number_of_correct_guesses) )
        # BONUS SCORE CALCULATION
        if not word_was_guessed or set(self.__chosen_word) == set(self.cguesses):
            res["BONUS"] = 0
        else:
            res["BONUS"] = GAMEVARS["MAX_BONUS_POINTS"] * ((number_of_letters_in_word - number_of_correct_guesses) / number_of_letters_in_word)
        # PENALTY CALCULATION
        res["PENALTY"] = GAMEVARS["PENALTY_FOR_HINT"] * self.hints_count + GAMEVARS["PENALTY_FOR_FALSE_GUESS"] * self.wrong_guess_count
        # COMPENSATION CALCULATION
        res["COMPENSATION"] = GAMEVARS["COMPENSATION_FOR_RANDOM"] if self.word_was_random else 0
        res["ROUND_TOTAL"] = res["PROGRESSION"] + res["BASE"] + res["BONUS"] + res["PENALTY"] + res["COMPENSATION"]
        res["GAME_TOTAL"] = res["ROUND_TOTAL"] + total_score
        self.update_public_data("p1scoreboard" if self.gsr is self.p1 else "p2scoreboard", res)
    
    def player_choose_word(self, content : str) -> tuple:
        d = Dictionary()
        word = d.select_random_word() if content == "__RANDOM__" else content
        word = word.upper()
        if len(word) <= 2 and content != "__RANDOM__":
            return (True, "warning", "Word must be longer than 2 characters.")
        elif not d.check_if_word_exists(word):
            return (True, "warning", "Word does not exist in our dictionary.")
        else:
            self.update_private_data("__chosen_word", word)
            self.msg_pool.push(self.ex, {"msg_type": "update", "update_type": "__chosen_word", "content": self.__chosen_word})
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
        else:
            msg = {
                "msg_type": "notification",
                "show": True,
                "notification_type": "warning",
                "content": "The Executioner has changed the word.",
                "tag": "WORD_UPDATED"
            }
            # reset hints
            self.update_public_data("hints", [])
            self.hints_count = 0
            self.update_private_data("__chosen_word", new_word)
            self.msg_pool.push(self.gsr, msg)
            return (True, "success", "Word changed successfully!")

    def player_choose_hint(self, content):
        if content not in self.__hints:
            return (True, "warning", "Not a valid choice.")
        else:
            self.update_public_data("hints", self.hints.append(self.__hints[content]))
            del self.__hints[content]
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
        if word == self.__chosen_word: self.update_public_data("guessed_correctly", True)
        else: self.update_private_data("wrong_guess_count", self.wrong_guess_count + 1)

    def player_request_hint(self, content):
        def finish_condition_check():
            self.hints_count == len(self.hints)
        if not self.hint_timer.finished: return (False, "warning", "Cannot request hint at this moment.")
        else:
            self.hints_count += 1
            self.hint_timer.finish_condition_check = finish_condition_check
            self.hint_timer.start()

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
        self.msg_pool.push(
            player, {
                "msg_type": "notification", 
                "show": response[0],
                "notification_type": response[1], 
                "content": response[2],
                "tag": None
                }
            )
    
    def start_round(self):

        # set initial data for first half round.
        self.update_public_data("ex", self.p1)
        self.update_public_data("gsr", self.p2)
        self.update_public_data("board", [])
        self.update_public_data("cguesses", set())
        self.update_public_data("fguesses", set())
        self.update_public_data("hints", [])
        self.update_public_data("hint_requested", False)
        self.update_public_data("p1scoreboard", {"GAME_TOTAL" : 0})
        self.update_public_data("p2scoreboard", {"GAME_TOTAL" : 0})
        self.update_public_data("rotated", False)
        self.update_public_data("word_was_random", False)
        self.update_public_data("guessed_correctly", False)

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

        # handle pacing of second half round.
        self.update_public_data("round_state", GAMEVARS["ROUND_STATE_READY"])
        self.handle_ready_stage()
        self.update_public_data("round_state", GAMEVARS["ROUND_STATE_CHOOSING_WORD"])
        self.handle_choose_word_stage()
        self.update_public_data("round_state", GAMEVARS["ROUND_STATE_GUESSING_WORD"])
        self.handle_guess_word_stage()
        self.update_public_data("round_state", GAMEVARS["ROUND_STATE_RECESS"])
        self.handle_round_recess()