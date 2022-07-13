from game import Game
from profanity_filter import ProfanityFilter

PF = ProfanityFilter()

class Games:
    def __init__(self, msg_pool) -> None:
        self.msg_pool = msg_pool
        self.games = {}
        self.curr_id_count = 0
    
    def join_any_game(self, client):
        for id in self.games:
            if not self.games[id].full():
                self.games[id].add_player(client)
                client.game = self.games[id]
                if self.games[id].full():
                    self.games[id].start()
                return
        new_game = self.create_new_game()
        new_game.add_player(client)
        client.game = new_game

    def create_new_game(self):
        new_game = Game(self.msg_pool, games=self, id=self.curr_id_count)
        self.games[self.curr_id_count] = new_game
        self.curr_id_count += 1
        print(f"[GAME CREATED] Game with GID {new_game.id} created.")
        return new_game

    def join_game_by_id(self, id):
        pass

    def handle_player_msg(self, player, message):
        message_type = message["msg_type"]
        if message_type == "join":
            game_id = message["game_id"]
            if game_id == "__ANY__":
                self.join_any_game(player)
            else:
                # TODO
                pass
        else:
            if player.game is not None:
                if message["msg_type"] == "chat":
                    message["content"] = PF.censor(message["content"])
                elif message["msg_type"] == "action":
                    if message["action_type"] == "choose_word" or message["action_type"] == "change_word":
                        message["content"] = PF.censor(message["content"])
                player.game.handle_player_msg(player, message)

    def handle_player_disconnect(self, player):
        if player.game:
            player.game.handle_disconnect(player)
        del self.games[player.game.id]
    
    def handle_game_finish(self, game):
        game.p1.game = None
        game.p2.game = None
        print(f"[GAME FINISHED] Game with GID {game.id} finished.")
        del self.games[game.id]
