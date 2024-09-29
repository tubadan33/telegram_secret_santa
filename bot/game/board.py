# Board.py

import random

from constants.Cards import playerSets, gameStrings
from constants.Cards import policies
from game.State import State


class Board(object):
    def __init__(self, playercount, game):
        self.state = State()
        self.num_players = playercount
        self.fascist_track_actions = playerSets[self.num_players]["track"]
        self.policies = random.sample(policies, len(policies))
        self.game = game
        self.discards = []
        self.previous = []

    def reset_policies(self, game_policies):
        if len(game_policies) == 0:
            game_policies = random.sample(policies, len(policies))
        return game_policies

    def print_board(self):
        board = f"--- {gameStrings['Liberal']} acts ---\n"
        for i in range():
            if i < self.state.liberal_track:
                board += u"\u2716\uFE0F" + " "  # X
            elif i >= self.state.liberal_track and i == 4:
                board += u"\U0001F54A" + " "  # dove
            else:
                board += u"\u25FB\uFE0F" + " "  # empty
        board += f"\n--- {gameStrings['Fascist']} acts ---\n"
        for i in range(6):
            if i < self.state.fascist_track:
                board += u"\u2716\uFE0F" + " "  # X
            else:
                action = self.fascist_track_actions[i]
                if action == None:
                    board += u"\u25FB\uFE0F" + " "  # empty
                elif action == "policy":
                    board += u"\U0001F52E" + " "  # crystal
                elif action == "inspect":
                    board += u"\U0001F50E" + " "  # inspection glass
                elif action == "kill":
                    board += u"\U0001F5E1" + " "  # knife
                elif action == "win":
                    board += u"\u2620" + " "  # skull
                elif action == "choose":
                    board += u"\U0001F454" + " "  # tie

        board += "\n--- Election counter ---\n"
        for i in range(3):
            if i < self.state.failed_votes:
                board += u"\u2716\uFE0F" + " "  # X
            else:
                board += u"\u25FB\uFE0F" + " "  # empty

        board += "\n--- Presidential order  ---\n"
        for player in self.game.player_sequence:
            board += player.name + " " + u"\u27A1\uFE0F" + " "
        board = board[:-3]
        board += u"\U0001F501"
        board += "\n\nThere are " + str(len(self.policies)) + " policies left on the pile."
        if self.state.fascist_track >= 3:
            board += "\n\n" + u"\u203C\uFE0F" + f" Beware: If {gameStrings['Hitler']} gets elected as Chancellor the {gameStrings['Fascists']} win the game! " + u"\u203C\uFE0F"
        if len(self.state.not_hitlers) > 0:
            board += f"\n\nWe know that the following players are not {gameStrings['Hitler']} because they got elected as Chancellor after 3 {gameStrings['Fascist']} policies:\n"
            for nh in self.state.not_hitlers:
                board += nh.name + ", "
            board = board[:-2]
        return board
