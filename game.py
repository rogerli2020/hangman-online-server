import threading
import json
import time
from round import Round

GAMEVARS_PATH = "./gamevars.json"
with open(GAMEVARS_PATH, "r") as f:
    GAMEVARS = json.load(f)

HINT_LOCK = threading.Lock()

class Game:
    def __init__(self, msg_pool, games, id, p1=None, p2=None):
        self.msg_pool = msg_pool # msg pool is a top level object that stores all the messages that the server needs to send.
        self.games = games
        self.id = id
        self.p1 = p1
        self.p2 = p2
        self.thread = threading.Thread(target=self.start_game)
        self.current_round = None

        # public game data
        self.current_round_count = 0
        self.game_state = GAMEVARS["GAME_STATE_WAITING"]

        # other
        self.stopped_prematurely = False
    
    def start_game(self):
        self.handle_chat("SERVER", {"content": "WARNING: This game uses unmonitored outside resources that might return pornographic or violent content. Player discretion is advised."})
        self.update_public_data("game_state", GAMEVARS["GAME_STATE_READY"])
        time.sleep(GAMEVARS["TIME_FOR_READY"])
        self.update_public_data("game_state", GAMEVARS["GAME_STATE_IN_PROGRESS"])

        p1gt = 0
        p2gt = 0

        self.update_public_data("current_round_count", 1)
        while self.current_round_count <= GAMEVARS["MAX_ROUNDS"] and not self.stopped_prematurely:
            self.current_round = Round(self.msg_pool, self.p1, self.p2, hint_lock = HINT_LOCK)
            p1gt, p2gt = self.current_round.start_round(p1gt, p2gt)
            self.update_public_data("current_round_count", self.current_round_count + 1)
            if self.current_round_count > GAMEVARS["MAX_ROUNDS"]: break
        self.handle_game_end()

    def start(self):
        self.thread.start()
    
    def handle_game_end(self):
        self.update_public_data("game_state", GAMEVARS["GAME_STATE_FINISHED"])
        self.games.handle_game_finish(self)
    
    def handle_player_msg(self, player, msg):
        if msg["msg_type"] == "action":
            if self.current_round:
                self.current_round.handle_player_actions(player, msg)
        elif msg["msg_type"] == "chat":
            self.handle_chat(player, msg)

    def handle_chat(self, player, msg):
        msg = {
            "msg_type": "chat",
            "chat_type": "normal",
            "sender": player.name if player != "SERVER" else "SERVER",
            "content": msg["content"]
        }
        self.msg_pool.push(self.p1, msg)
        self.msg_pool.push(self.p2, msg)

    def add_player(self, player):
        if not self.p1:
            self.p1 = player
            self.msg_pool.push(player, {
                "msg_type": "update",
                "update_type": "game_state",
                "content": self.game_state
            })
        elif not self.p2 and self.p1.ws != player.ws:
            self.p2 = player
            self.msg_pool.push(player, {
                "msg_type": "update",
                "update_type": "game_state",
                "content": self.game_state
            })
    
    def full(self):
        return self.p1 is not None and self.p2 is not None
    
    def update_public_data(self, varname, data):
        def update_current_round_count(data):
            self.current_round_count = data
        def update_game_state(data):
            self.game_state = data
        mapping = {
            "current_round_count": update_current_round_count,
            "game_state": update_game_state
        }
        mapping[varname](data)
        msg = {
            "msg_type": "update",
            "update_type": varname,
            "content": data
        }
        self.msg_pool.push(self.p1, msg)
        self.msg_pool.push(self.p2, msg)

    def handle_disconnect(self, player):
        if self.current_round:
            if player == self.p1:
                self.current_round.update_public_data("p1scoreboard", {"ID": self.p1.id, "FINISHED_GUESSING": False, "GAME_TOTAL" : 0, "DISCONNECTED" : True})
            elif player == self.p2:
                self.current_round.update_public_data("p2scoreboard", {"ID": self.p2.id, "FINISHED_GUESSING": False, "GAME_TOTAL" : 0, "DISCONNECTED" : True})
            self.current_round.stopped_prematurely = True
            self.stopped_prematurely = True
        else:
            if player == self.p1:
                self.p1 = None
            elif player == self.p2:
                self.p2 = None