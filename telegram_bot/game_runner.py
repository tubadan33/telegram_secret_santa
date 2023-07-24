from constants.Cards import playerSets
from random import randrange
from telebot import types
import random
import re
from config import TEST

def start_round(bot, game):
    print('start_round called')
    if game.board.state.chosen_president is None:
        game.board.state.nominated_president = game.player_sequence[game.board.state.player_counter]
    else:
        game.board.state.nominated_president = game.board.state.chosen_president
        game.board.state.chosen_president = None
    bot.send_message(game.chat_id,
                     "The next presidential canditate is %s.\n%s, please nominate a Chancellor in our private chat!" % (
                         game.board.state.nominated_president.name, game.board.state.nominated_president.name))
    choose_chancellor(bot, game)
    # --> nominate_chosen_chancellor --> vote --> handle_voting --> count_votes --> voting_aftermath --> draw_policies
    # --> choose_policy --> pass_two_policies --> choose_policy --> enact_policy --> start_round

def choose_chancellor(bot, game):
    #log.info('choose_chancellor called')
    strcid = str(game.chat_id)
    pres_player = 0
    chan_player = 0
    btns = []
    if game.board.state.president is not None:
        pres_player = game.board.state.president.player
    if game.board.state.chancellor is not None:
        chan_player= game.board.state.chancellor.player
    for player in game.get_players():
        # If there are only five players left in the
        # game, only the last elected Chancellor is
        # ineligible to be Chancellor Candidate; the
        # last President may be nominated.
        if len(game.player_sequence) > 5:
            if player != game.board.state.nominated_president.player and game.get_players()[
                player].is_dead == False and player != pres_player and player != chan_player:
                name = game.get_players()[player].name
                btns.append([types.InlineKeyboardButton(name, callback_data=strcid + "_chan_" + str(player))])
        else:
            if player != game.board.state.nominated_president.player and game.get_players()[
                player].is_dead == False and player != chan_player:
                name = game.get_players()[player].name
                btns.append([types.InlineKeyboardButton(name, callback_data=strcid + "_chan_" + str(player))])

    chancellorMarkup = types.InlineKeyboardMarkup(btns)
    bot.send_message(game.board.state.nominated_president.player, game.board.print_board())
    bot.send_message(game.board.state.nominated_president.player, 'Please nominate your chancellor!',
                     reply_markup=chancellorMarkup)


def get_membership(role):
    print('get_membership called')
    if role == "Fascist" or role == "Blue":
        return "fascist"
    elif role == "Liberal":
        return "liberal"
    else:
        return None
    
def print_player_info(player_number):
    if player_number == 5:
        return "There are 3 Liberals, 1 Fascist and Hitler. Hitler knows who the Fascist is."
    elif player_number == 6:
        return "There are 4 Liberals, 1 Fascist and Hitler. Hitler knows who the Fascist is."
    elif player_number == 7:
        return "There are 4 Liberals, 2 Fascist and Hitler. Hitler doesn't know who the Fascists are."
    elif player_number == 8:
        return "There are 5 Liberals, 2 Fascist and Hitler. Hitler doesn't know who the Fascists are."
    elif player_number == 9:
        return "There are 5 Liberals, 3 Fascist and Hitler. Hitler doesn't know who the Fascists are."
    elif player_number == 10:
        return "There are 6 Liberals, 3 Fascist and Hitler. Hitler doesn't know who the Fascists are."

    
def inform_players(bot, game):
    player_number = len(game.get_players())
    available_roles = list(playerSets[player_number]["roles"])
    print(', '.join(str(player.user_id) for player in game.get_players()))

    for player in game.get_players():
        if not re.search('test', str(player.user_id)):
            random_index = randrange(len(available_roles))
            role = available_roles.pop(random_index)
            player.role = role
            player.party = get_membership(role)

            bot.send_message(player.user_id,
                                    "Your secret role is: %s\nYour party membership is: %s" % (role, get_membership(role)))
        else:
            #assign test roles without sending message to test players
            random_index = randrange(len(available_roles))
            role = available_roles.pop(random_index)
            party = get_membership(role)
            player.role = role
            player.party = party

    bot.send_message(game.chat_id,
                           "Let's start the game with %d players!\n%s\nCheck your private messages for your secret role!" % (
                               player_number, print_player_info(player_number)))
    

def inform_fascists(bot, game):
    player_number = len(game.get_players())

    for player in game.get_players():
        role = player.role
        print("ROLE: ", role)
        if role == "Fascist":
            fascists = [p for p in game.get_players() if p.role == "Fascist" and p.user_id != player.user_id]
            hitler = next(p for p in game.get_players() if p.role == "Hitler")
            if player_number > 6:
                fstring = ", ".join([f.name for f in fascists])
                if not re.search('test', str(player.user_id)):
                    bot.send_message(player.user_id, "Your fellow fascists are: %s" % fstring)
            if not re.search('test', str(player.user_id)):
                bot.send_message(player.user_id, "Blue is: %s" % hitler.name)
        elif role == "Hitler":
            if player_number <= 6:
                fascist = next(p for p in game.get_players() if p.role == "Fascist")
                if not re.search('test', str(player.user_id)):
                    bot.send_message(player.user_id, "Your fellow fascist is: %s" % fascist.name)
        elif role == "Liberal":
            pass
        else:
            print("inform_fascists: can't handle the role %s" % role)

def increment_player_counter(game):
    #log.info('increment_player_counter called')
    if game.board.state.player_counter < len(game.player_sequence) - 1:
        game.board.state.player_counter += 1
    else:
        game.board.state.player_counter = 0
        
def shuffle_policy_pile(bot, game):
#log.info('shuffle_policy_pile called')
    if len(game.board.policies) < 3:
        game.board.discards += game.board.policies
        game.board.policies = random.sample(game.board.discards, len(game.board.discards))
        game.board.discards = []
        bot.send_message(game.chat_id,
                        "There were not enough cards left on the policy pile so I shuffled the rest with the discard pile!")
