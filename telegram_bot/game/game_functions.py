from game.board import Board
from game.player import Player
from constants.Cards import playerSets
from constants.Cards import policies
import random
from game.test_player import TestPlayer
import game_runner 
from gamecontroller import GamesController

class SecretHitlerGame:
    def __init__(self, chat_id, initiator_id, player_count=None):
        self.chat_id = chat_id
        self.initiator_id = initiator_id 
        self.players = {}
        self.player_sequence = []
        self.game_phase = "waiting_for_players"
        self.board = None  # Board will be initialized later
        self.policy_deck = policies.copy()  # copies the original policies deck
        random.shuffle(self.policy_deck)  # shuffles the deck
        self.policies_in_play = []  # holds policies that are currently in play
        self.liberal_policies_passed = 0  # keeps count of liberal policies passed
        self.fascist_policies_passed = 0  # keeps count of fascist policies passed
        self.fascist_track_actions = None  # Will be set when player count is known
        self.player_count = player_count  # It can be None at this point

    def set_player_count(self, player_count):
        self.player_count = player_count
        self.board = Board(player_count, self)
        self.fascist_track_actions = playerSets[player_count]["track"]

    def add_player(self, user_id, name): 
        player = Player(user_id, name) 
        self.players[user_id] = player
        self.player_sequence.append(player)

    def get_players(self):
        return list(self.players.values())

    def start_game(self, bot, game):
        self.game_phase = "game_started"
        self.set_player_count(len(self.players)) 
        self.assign_roles()

        player_number = len(self.get_players())
        
        # Inform players and fascists about their roles
        game_runner.inform_players(bot, game)
        game_runner.inform_fascists(bot, game)
        
        random.shuffle(self.player_sequence)  # shuffle player order at the start
        
        # Start a new round
        game_runner.start_round(bot, game)

        return "The game has started!"
    
    def assign_roles(self):
        roles = playerSets[len(self.players)]["roles"]
        random.shuffle(roles)
        for player, role in zip(self.players.values(), roles):
            player.role = role

    def add_test_players(self, player_gap):
        for i in range(player_gap):
            test_player = TestPlayer(f'test{i}', f'Test Player {i}')
            print("TEST: ", test_player.user_id)
            self.add_player(test_player.user_id, test_player.name)
            
    def get_board(self):
        return self.board

def create_new_game(player_count=None):
    return SecretHitlerGame(player_count)