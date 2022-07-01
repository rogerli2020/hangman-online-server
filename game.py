import threading
import json
import time
from round import Round

GAMEVARS_PATH = "./gamevars.json"
with open(GAMEVARS_PATH, "r") as f:
    GAMEVARS = json.load(f)

class Game:
    def __init__(self, msg_pool, id, p1=None, p2=None):
        self.msg_pool = msg_pool # msg pool is a top level object that stores all the messages that the server needs to send.
        self.id = id
        self.p1 = p1
        self.p2 = p2
        self.thread = threading.Thread(target=self.start_game)
        self.current_round = None

        # public game data
        self.current_round_count = 0
        self.game_state = GAMEVARS["GAME_STATE_WAITING"]
    
    def start_game(self):
        self.update_public_data("game_state", GAMEVARS["GAME_STATE_READY"])
        time.sleep(GAMEVARS["TIME_FOR_READY"])
        self.update_public_data("game_state", GAMEVARS["GAME_STATE_IN_PROGRESS"])

        p1gt = 0
        p2gt = 0

        self.update_public_data("current_round_count", 1)
        while self.current_round_count <= GAMEVARS["MAX_ROUNDS"]:
            self.current_round = Round(self.msg_pool, self.p1, self.p2)
            p1gt, p2gt = self.current_round.start_round(p1gt, p2gt)
            self.update_public_data("current_round_count", self.current_round_count + 1)
            if self.current_round_count > GAMEVARS["MAX_ROUNDS"]: break
        self.update_public_data("game_state", GAMEVARS["GAME_STATE_FINISHED"])

    def start(self):
        self.thread.start()
    
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
            "sender": player.name,
            "content": msg["content"]
        }
        self.msg_pool.push(self.p1, msg)
        self.msg_pool.push(self.p2, msg)

    def add_player(self, player):
        if not self.p1:
            self.p1 = player
        elif not self.p2:
            self.p2 = player
    
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
    
    def stop_game(self):
        self.update_public_data("game_state", GAMEVARS["GAME_STATE_FINISHED"])

    def disconnect_player(self, player):
        pass