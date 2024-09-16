import pickle


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

    """  
    # Testing different game state saving methods
    # -> json
    @classmethod
    def save_game_state(cls, chat_id, filename="game_state.json"):
        dir = "state_save/"
        print(filename)
        with open(str(dir + filename), "w") as file:
            json.dump(cls.games.get(chat_id, None).to_dict(), file)
        return cls.games.get(chat_id, None)   
    """

    @classmethod
    def save_game_state(cls, chat_id, filename="game_state.pkl"):
        dir = "state_save/"
        with open(dir + filename, "wb") as file:
            pickle.dump(cls.games.get(chat_id, None), file)

    @classmethod
    def load_game_state(cls, chat_id, filename="game_state.pkl"):
        dir = "state_save/"
        with open(dir + filename, "rb") as file:
            loaded_game = pickle.load(file)
            if loaded_game:
                cls.games[chat_id] = loaded_game
            else:
                print("Could not load game state")

    def get_players(self):
        return self.players

    def set_game_instance(self, game_instance):
        self.game_instance = game_instance

