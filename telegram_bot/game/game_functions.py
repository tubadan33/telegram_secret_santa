from game.board import Board
from game.player import Player
from constants.Cards import playerSets
from constants.Cards import policies
import random
import time
from game.test_player import TestPlayer
import game_runner 

class SecretHitlerGame:
    def __init__(self, chat_id, initiator_id, player_count=None):
        self.chat_id = chat_id
        self.initiator_id = initiator_id 
        self.players = {}
        self.player_sequence = []
        self.upcoming_turns = []
        self.dateinitvote = None
        self.votes = {} 
        self.game_phase = "waiting_for_players"
        self.board = None 
        self.policy_deck = policies.copy()  
        random.shuffle(self.policy_deck)  
        self.policies_in_play = []  
        self.liberal_policies_passed = 0  
        self.fascist_policies_passed = 0  
        self.fascist_track_actions = None  
        self.player_count = player_count 
        self.turn = None 
        self.choose_president_turn = None
        ## Voting Timeout ##
        self.user_vote_timers = {}
        self.vote_messages = {}
        
    def set_player_count(self, player_count):
        self.player_count = player_count
        self.board = Board(player_count, self)
        self.fascist_track_actions = playerSets[player_count]["track"]

    def add_player(self, user_id, name): 
        player = Player(user_id, name) 
        self.players[user_id] = player
        self.player_sequence.append(player)

    def get_game_phase(self):
        return self.game_phase

    def get_players(self):
        return list(self.players.values())
    
    def get_player_name_by_id(self, user_id):
        for player in self.get_players():
            if player.user_id == user_id:
                return player.name
        return None  


    def start_game(self, bot, game):
        self.game_phase = "game_started"
        self.upcoming_turns = self.player_sequence.copy() 
        self.set_player_count(len(self.players)) 
        self.assign_roles()

        player_number = len(self.get_players())
        game_runner.inform_players(bot, game)
        game_runner.inform_fascists(bot, game)

        random.shuffle(self.player_sequence) 
        self.upcoming_turns = self.player_sequence.copy()  

        game_runner.start_round(bot, game)

        return "The game has started!"
    
    def next_turn(self):
        if len(self.upcoming_turns) == 0:
            self.upcoming_turns = self.player_sequence.copy()  # Refresh the turn queue when it's empty
        next_player = self.upcoming_turns.pop(0)  # Dequeue the next player
        self.board.state.nominated_president = next_player  # Ensure the nominated president is always the current player
        return next_player
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
    
    def get_players_alive(self):
        players_alive = []
        players = self.get_players()
        for player in players:
            if player.alive:
                players_alive.append(player)
        return players_alive
    
    def print_roles(self):
        rtext = ""
        if self.board is None:
            return rtext
        else:
            for player in self.get_players():
                rtext += player.name + "'s "
                if not player.alive:
                    rtext += "(dead) "
                rtext += "secret role was " + player.role + "\n"
            return rtext
        
    def get_user_timer(self, user_id):
        return self.user_vote_timers.get(user_id, None)
    
    def clear_user_timers(self):
        self.user_vote_timers.clear()

    def set_user_timer(self, user_id, timer):
        self.user_vote_timers[user_id] = timer

    def delete_user_timer(self, user_id):
        if user_id in self.user_vote_timers:
            del self.user_vote_timers[user_id]  

    def clear_vote_messages(self):
        self.vote_messages.clear()

   # def get_vote_messages(self, user_id):
    #    return self.user_vote_timers.get(user_id, None)   
    
def create_new_game(player_count=None):
    return SecretHitlerGame(player_count)