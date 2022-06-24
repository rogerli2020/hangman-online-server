from game import Game

class Games:
    def __init__(self, msg_pool) -> None:
        self.msg_pool = msg_pool
        self.games = {}
        self.current_game_id_count = 0
    
    def find_any_game(self, player):
        for g in self.games:
            if not g.is_full():
                g.add_player(player)
                return g
        g = self.create_new_game()
        g.add_player(player)
        if g.full():
            g.start()
    
    def create_new_game(self):
        self.current_game_id_count += 1
        new_game = Game(msg_pool=self.msg_pool, id=self.current_game_id_count)
        self.games[self.current_game_id_count] = new_game
        return new_game