from game import Game

class Games:
    def __init__(self, msg_pool) -> None:
        self.msg_pool = msg_pool
        self.games = {}
        self.curr_id_count = 0
    
    def join_any_game(self, client):
        for id in self.games:
            if not self.games[id].full():
                self.games[id].add_player(client)
                return self.games[id]
        new_game = self.create_new_game()
        new_game.add_player(client)
        return new_game

    def stop_game(self, id):
        pass

    def create_new_game(self):
        new_game = Game(self.msg_pool, id=self.curr_id_count)
        self.curr_id_count += 1
        self.games[self.curr_id_count] = new_game
        return new_game

    def join_game_by_id(self, id):
        pass