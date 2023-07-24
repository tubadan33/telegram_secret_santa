class GamesController:
    games = {}

    @classmethod
    def new_game(cls, chat_id, game):
        cls.games[chat_id] = game

    @classmethod
    def end_game(cls, chat_id):
        if chat_id in cls.games:
            del cls.games[chat_id]

    @classmethod
    def get_game(cls, chat_id):
        return cls.games.get(chat_id, None)
    
    def get_players(self):
        return self.players

    def set_game_instance(self, game_instance):
        self.game_instance = game_instance