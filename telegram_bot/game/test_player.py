from game.player import Player
import random


class TestPlayer(Player):
    def __init__(self, user_id, name):
        super().__init__(user_id, name)

    def vote(self):
        return random.choice(['yes', 'no'])

    def choose_policy(self):
        return random.choice(['liberal', 'fascist'])