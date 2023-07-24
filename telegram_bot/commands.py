
import os
from config import TOKEN, TEST
import telebot
from game.player import Player
from game.board import Board
from game.game_functions import create_new_game, SecretHitlerGame
import requests
from gamecontroller import GamesController
from game.test_player import TestPlayer
from game_runner import inform_players, print_player_info, inform_fascists

bot = telebot.TeleBot(TOKEN)

games = {}  # a dictionary to store ongoing games


commands = [  # command description used in the "help" command
    '/help - Gives you information about the available commands',
    '/start - Gives you a short piece of information about Secret Blue',
    '/symbols - Shows you all possible symbols of the board',
    '/rules - Gives you a link to the official Secret Blue rules',
    '/newgame - Creates a new game',
    '/join - Joins an existing game',
    '/startgame - Starts an existing game when all players have joined',
    '/cancelgame - Cancels an existing game. All data of the game will be lost',
    '/board - Prints the current board with fascist and liberals tracks, presidential order and election counter',
    '/votes - Prints who voted',
    '/calltovote - Calls the players to vote'
]

symbols = [
    u"\u25FB\uFE0F" + ' Empty field without special power',
    u"\u2716\uFE0F" + ' Field covered with a card',  # X
    u"\U0001F52E" + ' Presidential Power: Policy Peek',  # crystal
    u"\U0001F50E" + ' Presidential Power: Investigate Loyalty',  # inspection glass
    u"\U0001F5E1" + ' Presidential Power: Execution',  # knife
    u"\U0001F454" + ' Presidential Power: Call Special Election',  # tie
    u"\U0001F54A" + ' Liberals win',  # dove
    u"\u2620" + ' Fascists win'  # skull
]

bot = telebot.TeleBot(TOKEN)
bot.set_webhook()
games = {}

@bot.message_handler(commands=['help'])
def help(message):
    chat_id = message.chat.id
    help_text = "The following commands are available:\n"
    for i in commands:
        help_text += i +"\n"
    bot.send_message(chat_id, help_text)


@bot.message_handler(commands=['start'])
def start_game(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "\"Secret Blue is a social deduction game for 5-10 people about finding and stopping the Secret Blue."
                     " The majority of players are liberals. If they can learn to trust each other, they have enough "
                     "votes to control the table and win the game. But some players are fascists. They will say whatever "
                     "it takes to get elected, enact their agenda, and blame others for the fallout. The liberals must "
                     "work together to discover the truth before the fascists install their cold-blooded leader and win "
                     "the game.\"\n- official description of Secret Blue\n\nAdd me to a group and type /newgame to create a game!")



@bot.message_handler(commands=['newgame'])
def newgame(message):
    chat_id = message.chat.id
    game = GamesController.get_game(chat_id)
    groupType = message.chat.type
    if groupType not in ['group', 'supergroup']:
        bot.send_message(chat_id, "You have to add me to a group first and type /newgame there!")
    elif game:
        bot.send_message(chat_id, "There is currently a game running. If you want to end it please type /cancelgame!")
    else:
        new_game = SecretHitlerGame(chat_id, message.from_user.id)  # 0 as a placeholder for player_count, it will be replaced when the game starts.
        GamesController.new_game(chat_id, new_game)
        bot.send_message(chat_id, "New game created! Each player has to /join the game.\nThe initiator of this game (or the admin) can /join too and type /startgame when everyone has joined the game!")

@bot.message_handler(commands=['startgame'])
def start_game(message):
    chat_id = message.chat.id
    game = GamesController.get_game(chat_id)
    if game is None:
        bot.send_message(chat_id, "There is no game in this chat. Create a new game with /newgame")
    elif game.game_phase == "game_started":
        bot.send_message(chat_id, "The game is already running!")
        #and not is_admin(message.from_user.id, chat_id)
    elif message.from_user.id != game.initiator_id: 
        bot.send_message(chat_id, "Only the initiator of the game or a group admin can start the game with /startgame")
    elif len(game.players) < 5:
        if TEST:
           game.add_test_players(player_gap=( 5 - len(game.players)))
        bot.send_message(chat_id, "There are not enough players (min. 5, max. 10). Join the game with /join")
    else:
        start_message = game.start_game(bot, game)
        bot.send_message(chat_id, start_message)

@bot.message_handler(commands=['join'])
def join(message):
    group_name = message.chat.title 
    chat_id = message.chat.id
    groupType = message.chat.type
    game = GamesController.get_game(chat_id)
    fname = message.from_user.first_name

    if groupType not in ['group', 'supergroup']:
        bot.send_message(chat_id, "You have to add me to a group first and type /newgame there!")
    elif not game:
        bot.send_message(chat_id, "There is no game in this chat. Create a new game with /newgame")
    elif game.game_phase != "waiting_for_players":
        bot.send_message(chat_id, "The game has started. Please wait for the next game!")
    elif message.from_user.id in game.players:
        bot.send_message(chat_id, "You already joined the game, %s!" % fname)
    elif len(game.players) >= 10:
        bot.send_message(chat_id, "You have reached the maximum amount of players. Please start the game with /startgame!")
    else:
        uid = message.from_user.id
        game.add_player(uid, fname)
        try:
            bot.send_message(uid, f"You joined a game in {group_name}. I will soon tell you your secret role.")
        except Exception:
            bot.send_message(chat_id, 
                             fname + ", I can't send you a private message. Please go to Bot's chat and click 'Start'.\nYou then need to send /join again.")
        else:
            if len(game.players) > 4:
                bot.send_message(chat_id, 
                                 fname + " has joined the game. Type /startgame if this was the last player and you want to start with %d players!" % len(game.players))
            else:
                bot.send_message(chat_id, 
                                 "%s has joined the game. There are currently %d players in the game and you need 5-10 players." % (fname, len(game.players)))

@bot.message_handler(commands=['cancelgame'])
def cancel_game(message):
    chat_id = message.chat.id
    game = GamesController.get_game(chat_id)
    #or is_admin(message.from_user.id, chat_id)
    if game:
        if message.from_user.id == game.initiator_id:
            GamesController.end_game(chat_id)
            bot.reply_to(message, "The game has been cancelled.")
        else:
            bot.reply_to(message, "Only the initiator of the game or a group admin can cancel the game with /cancelgame")
    else:
        bot.reply_to(message, "There is no game in this chat. Create a new game with /newgame")

@bot.message_handler(commands=['board'])
def show_board(message):
    chat_id = message.chat.id
    game = GamesController.get_game(chat_id)
    if game:
        board = game.get_board().print_board()
        bot.send_message(chat_id, board)
    else:
        bot.send_message(chat_id, "No game in progress.")

@bot.message_handler(commands=['help'])
def send_help(message):
    chat_id = message.chat.id
    help_text = "Here are the available commands:\n" + "\n".join(commands)
    bot.send_message(chat_id, help_text)

@bot.message_handler(commands=['symbols'])
def send_symbols(message):
    chat_id = message.chat.id
    symbols_text = "Here are the game symbols:\n" + "\n".join(symbols)
    bot.send_message(chat_id, symbols_text)

bot.infinity_polling()