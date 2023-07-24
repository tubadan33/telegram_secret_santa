from game.player import Player
import random


class TestPlayer(Player):
    def __init__(self, user_id, name):
        super().__init__(user_id, name)

    def vote(self):
        # For testing, we can return a random vote (either 'yes' or 'no')
        return random.choice(['yes', 'no'])

    def choose_policy(self):
        # Similarly, we can return a random policy choice
        return random.choice(['liberal', 'fascist'])