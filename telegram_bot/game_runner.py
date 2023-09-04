from constants.Cards import playerSets
from gamecontroller import GamesController
from random import randrange
from telebot import types
import random
import datetime
import time
import re
from config import TEST
import threading
from apscheduler.schedulers.background import BackgroundScheduler
test_timeout = False
scheduler = BackgroundScheduler()
scheduler.start()
def start_round(bot, game):
    print('start_round called')
    if game.turn is None:
        game.turn = 0
    elif game.board.state.chosen_president is None:
        game.turn = (game.turn + 1) % len(game.player_sequence)

    # Choose the next president
    print("DEBUG PRESIDENT: ", game.board.state.chosen_president)
    if game.board.state.chosen_president is None:
        print("game.turn: ", game.turn, " Sequence: ",  game.player_sequence[game.turn].name)
        game.board.state.nominated_president = game.player_sequence[game.turn]
    else:
        game.board.state.nominated_president = game.board.state.chosen_president
        game.board.state.chosen_president = None

    bot.send_message(game.chat_id,
                     "The next presidential candidate is %s.\n%s, please nominate a Chancellor in our private chat!" % (
                         game.board.state.nominated_president.name, game.board.state.nominated_president.name))
    print("Round Starting, nom pres ", game.board.state.nominated_president)
    choose_chancellor(bot, game)

def choose_chancellor(bot, game):
    print('choose_chancellor called')

    # Add this check at the beginning of your function
    if game.player_sequence[game.turn].user_id != game.board.state.nominated_president.user_id:
        print('It is not the turn of', game.board.state.nominated_president.name, 'to nominate a chancellor')
        return

    strcid = str(game.chat_id)
    pres_player = None
    chan_player = None
    btns = []
    if game.board.state.president is not None:
        pres_player = game.board.state.president.user_id
    if game.board.state.chancellor is not None:
        chan_player = game.board.state.chancellor.user_id
    for player in game.get_players():
        if len(game.get_players()) > 5:
            if player.user_id != game.board.state.nominated_president.user_id and player.alive == True and player.user_id != pres_player and player.user_id != chan_player:
                btns.append([types.InlineKeyboardButton(player.name, callback_data=strcid + "_choose_chancellor_" + str(player.user_id))])
        else:
            if player.user_id != game.board.state.nominated_president.user_id and player.alive == True and player.user_id != chan_player:
                btns.append([types.InlineKeyboardButton(player.name, callback_data=strcid + "_choose_chancellor_" + str(player.user_id))])

    chancellorMarkup = types.InlineKeyboardMarkup(btns)
    if not re.search('test', str(game.board.state.nominated_president.user_id)):
        bot.send_message(game.board.state.nominated_president.user_id, game.board.print_board())
        bot.send_message(game.board.state.nominated_president.user_id, 'Please nominate your chancellor!',
                         reply_markup=chancellorMarkup)
    else:  # case for test player
        # pick the first available player as chancellor
        for player in game.get_players():
            if  re.search('test', str(player.user_id)):
                if player.user_id != game.board.state.nominated_president.user_id and player.alive == True and player.user_id != chan_player:
                    # simulate the callback logic
                    print(f"Simulating callback with data: {strcid}, {player.user_id}")
                    # Find the player instance by user ID
                    chosen_chancellor = next((p for p in game.get_players() if p.user_id == player.user_id), None)
                    print("CHOSEN BOT CHANCELLOR: ", chosen_chancellor.name)
                    if chosen_chancellor is None:
                        print("Unknown player")
                        return
                    game.board.state.nominated_chancellor = chosen_chancellor
                    if game.board.state.nominated_chancellor is not None:
                        print("You nominated %s as Chancellor!" % game.board.state.nominated_chancellor.name)
                    else:
                        print("Error: No suitable player found to nominate as chancellor")
                    nominate_chosen_chancellor(bot, game)
                    break
def nominate_chosen_chancellor(bot, game):
    print('TEST PLAYER nominate_chosen_chancellor called')
    print("President %s (%s) nominated %s (%s)" % (
        game.board.state.nominated_president.name, game.board.state.nominated_president.user_id,
        game.board.state.nominated_chancellor.name, game.board.state.nominated_chancellor.user_id))
    #if not re.search('test', str(game.board.state.nominated_president.user_id)):
    bot.send_message(game.chat_id,
                        "President %s nominated %s as Chancellor. Please vote now!" % (
                            game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name))
                            
    vote(bot, game)


def handle_vote_timeout(bot, player, game):
    # Check if the user has already voted
    if player.user_id not in game.votes:
        # Cast a random vote
        random_vote = random.choice(["Ja", "Nein"])
        game.votes[player.user_id] = random_vote
        message_id = game.vote_messages.get(player.user_id)
        print(message_id)
        if message_id:
            bot.edit_message_text(chat_id=player.user_id, message_id=message_id,
                                    text="You took too long to vote. A random vote was casted for you.")
        timer = game.get_user_timer(player.user_id)
        game.clear_vote_messages()
        timer.cancel()
        game.delete_user_timer(player.user_id)
        print("Cleared Timer")
        start_bot_voting(bot, game)
        timer.cancel()
        del timer

def check_and_count_votes(bot, game):
    if len(game.votes) == len(game.get_players()):
        count_votes(bot, game)

def vote(bot, game):
    print('vote called')
    
    game.dateinitvote = datetime.datetime.now()
    strcid = str(game.chat_id)
    bot_throttle = 8
    real_players = [player for player in game.get_players() if not re.search('test', str(player.user_id)) and player.alive]
    
    if len(real_players) == 0:
        print("Bot Only Voiting in Progress.....Throttle bots by {} seconds.".format(bot_throttle))
        time.sleep(bot_throttle)
        start_bot_voting(bot, game)
        return
    
    for player in real_players:
        # Create vote buttons for this specific player
        btns = [[types.InlineKeyboardButton("Ja", callback_data=f"{strcid}_vote_{player.user_id}_Ja")],
                [types.InlineKeyboardButton("Nein", callback_data=f"{strcid}_vote_{player.user_id}_Nein")]
        ]
        voteMarkup = types.InlineKeyboardMarkup(btns)
        
        bot.send_message(player.user_id, game.board.print_board())
        vote_message = bot.send_message(player.user_id,
                            "Do you want to elect President %s and Chancellor %s?" % (
                                game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name),
                            reply_markup=voteMarkup)
        print("MESSAGE ID: ", vote_message.message_id)
        game.vote_messages[player.user_id] = vote_message.message_id
        timer = threading.Timer(30, handle_vote_timeout, args=[bot, player, game])
        timer.start()
        game.set_user_timer(player.user_id, timer)

        
def start_bot_voting(bot,game):
    print("STARTING BOT VOTING")
    for player in game.get_players():
        if  re.search('test', str(player.user_id)):
            if player.alive:
                player_vote = random.choice(["Ja", "Nein"])
                game.votes[player.user_id] = player_vote
                print(f"Test player {player.name} ({player.user_id}) voted {player_vote}")
    check_and_count_votes(bot, game)

def check_and_count_votes(bot, game):
    print('check_and_count_votes called')
    print(f'Current votes: {game.votes}')
    print(f'Total number of players: {len(game.get_players())}')
    print(f'Number of votes needed for counting: {len(game.get_players_alive())}')

    if len(game.votes) == len(game.get_players_alive()):
        print('All votes have been collected, proceeding to count votes')
        count_votes(bot, game)
    else:
        print('Not all votes have been collected yet')

def count_votes(bot, game):
    print('count_votes called')
    print(f"Votes: {game.votes}")
    print(f"Number of players: {len(game.get_players())}")
    # Voting Ended
    game.dateinitvote = None
    voting_text = ""
    voting_success = False
    for player in game.player_sequence:
        if game.votes[player.user_id] == "Ja":
            voting_text += player.name + " voted Ja!\n"
        elif game.votes[player.user_id] == "Nein":
            voting_text += player.name + " voted Nein!\n"
    if list(game.votes.values()).count("Ja") > len(game.get_players_alive()) / 2:
        # VOTING WAS SUCCESSFUL
        print("Voting successful")
        voting_text += "Hail President %s! Hail Chancellor %s!" % (
            game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
        game.board.state.chancellor = game.board.state.nominated_chancellor
        game.board.state.president = game.board.state.nominated_president
        game.board.state.nominated_president = None
        game.board.state.nominated_chancellor = None
        bot.send_message(game.chat_id, voting_text)  # Send the message before setting to None
        voting_success = True
        voting_aftermath(bot, game, voting_success)
        # Set nominated_president and nominated_chancellor to None after they're no longer needed
        print("SETTING PRES CHANCE TO NONE during SUCCESS")       

    else:
        print("Voting failed")
        print("GAMES VOTES CLEARED: ", game.votes)
        voting_text += "The people didn't like the two candidates!"
        print("SETTING PRES CHANCE TO NONE during FAILED")       
        game.board.state.nominated_president = None
        game.board.state.nominated_chancellor = None
        game.board.state.failed_votes += 1
        bot.send_message(game.chat_id, voting_text)
        if game.board.state.failed_votes == 3:
            do_anarchy(bot, game)

        else:
            voting_aftermath(bot, game, voting_success)

def voting_aftermath(bot, game, voting_success):
    print('voting_aftermath called')
    game.board.state.last_votes = {}
    game.votes.clear()
    if voting_success:
        if game.board.state.fascist_track >= 3 and game.board.state.chancellor.role == "Hitler":
            # fascists win, because Hitler was elected as chancellor after 3 fascist policies
            game.board.state.game_endcode = -2
            end_game(bot, game, game.board.state.game_endcode)
        elif game.board.state.fascist_track >= 3 and game.board.state.chancellor.role != "Hitler" and game.board.state.chancellor not in game.board.state.not_hitlers:
            game.board.state.not_hitlers.append(game.board.state.chancellor)
            draw_policies(bot, game)
        else:
            # voting was successful and Hitler was not nominated as chancellor after 3 fascist policies
            draw_policies(bot, game)
    else:
        bot.send_message(game.chat_id, game.board.print_board())
        start_next_round(bot, game)  # Start a new round directly instead of calling start_next_round

def draw_policies(bot, game):
    print('draw_policies called')
    strcid = str(game.chat_id)
    game.board.state.veto_refused = False
    # Ensure that there are enough policies to draw from
    shuffle_policy_pile(bot, game)
    # Stop the function if there are still not enough policies
    if len(game.board.policies) < 3:
        bot.send_message(game.chat_id, "There aren't enough policies to draw!")
        return  # Or handle this situation as you see fit
    
    # Clear the drawn_policies list
    game.board.state.drawn_policies = []

    btns = []
    for i in range(3):
        game.board.state.drawn_policies.append(game.board.policies.pop(0))
    
    for policy in game.board.state.drawn_policies:
        btns.append([types.InlineKeyboardButton(policy, callback_data=strcid + "_" + policy)])

    choosePolicyMarkup = types.InlineKeyboardMarkup(btns)
    
    # Handle user or bot drawing policies
    if not re.search('test', str(game.board.state.president.user_id)):
        bot.send_message(game.board.state.president.user_id,
                         "You drew the following 3 policies. Which one do you want to discard?",
                         reply_markup=choosePolicyMarkup)
    else:  # case for test player
        discarded_policy = random.choice(game.board.state.drawn_policies)
        game.board.state.drawn_policies.remove(discarded_policy)
        print(f"Test player {game.board.state.president.name} ({game.board.state.president.user_id}) discarded {discarded_policy}")
        pass_two_policies(bot, game)

def pass_two_policies(bot, game):
    print('pass_two_policies called')
    strcid = str(game.chat_id)
    btns = []
    for policy in game.board.state.drawn_policies:
        btns.append([types.InlineKeyboardButton(policy, callback_data=strcid + "_" + policy)])
    choosePolicyMarkup = types.InlineKeyboardMarkup(btns)

    if len(game.board.state.drawn_policies) != 2:
        print(f"Error: expected 2 policies but got {len(game.board.state.drawn_policies)}")

    is_test_player = re.search('test', str(game.board.state.chancellor.user_id))

    if game.board.state.fascist_track == 5 and not game.board.state.veto_refused:
        btns.append([types.InlineKeyboardButton("Veto", callback_data=strcid + "_veto")])
        if not is_test_player:
            bot.send_message(game.chat_id,
                             "President %s gave two policies to Chancellor %s." % (
                                 game.board.state.president.name, game.board.state.chancellor.name))
            bot.send_message(game.board.state.chancellor.user_id,
                             "President %s gave you the following 2 policies. Which one do you want to enact? You can also use your Veto power." % game.board.state.president.name,
                             reply_markup=choosePolicyMarkup)
        else:
            handle_test_player_choice(bot, game)

    elif game.board.state.veto_refused:
        if not is_test_player:
            bot.send_message(game.board.state.chancellor.user_id,
                             "President %s refused your Veto. Now you have to choose. Which one do you want to enact?" % game.board.state.president.name,
                             reply_markup=choosePolicyMarkup)
        else:
            handle_test_player_choice(bot, game)

    elif game.board.state.fascist_track < 5:
        if not is_test_player:
            bot.send_message(game.board.state.chancellor.user_id,
                             "President %s gave you the following 2 policies. Which one do you want to enact?" % game.board.state.president.name,
                             reply_markup=choosePolicyMarkup)
        else:
            handle_test_player_choice(bot, game)

def handle_test_player_choice(bot, game):
    # Randomly select a policy
    policy_choice = random.choice(game.board.state.drawn_policies)
    print(f"Test player {game.board.state.chancellor.user_id} chose {policy_choice}")
    # Implement logic here to handle the test player's chosen policy
    game.board.state.drawn_policies.remove(policy_choice)
    # Enact the chosen policy
    time.sleep(2)  # wait for 2 seconds
    enact_policy(bot, game, policy_choice, False)  # assuming anarchy = False

def enact_policy(bot, game, policy, anarchy):
    print('enact_policy called')
    
    if policy == "liberal":
        game.board.state.liberal_track += 1
    elif policy == "fascist":
        game.board.state.fascist_track += 1
    
    game.board.state.failed_votes = 0  # reset counter
    
    if not anarchy:
        bot.send_message(game.chat_id,
                         "President %s and Chancellor %s enacted a %s policy!" % (
                             game.board.state.president.name, game.board.state.chancellor.name, policy))
    else:
        bot.send_message(game.chat_id,
                         "The top most policy was enacted: %s" % policy)

    time.sleep(3)
    bot.send_message(game.chat_id, game.board.print_board())
    # end of round
    if game.board.state.liberal_track == 5:
        game.board.state.game_endcode = 1
        end_game(bot, game, game.board.state.game_endcode)  # liberals win with 5 liberal policies
    if game.board.state.fascist_track == 6:
        game.board.state.game_endcode = -1
        end_game(bot, game, game.board.state.game_endcode)  # fascists win with 6 fascist policies

    time.sleep(3)
    # End of legislative session, shuffle if necessary 
    shuffle_policy_pile(bot, game)    
    
    if not anarchy:
        if policy == "fascist":
            action = game.board.fascist_track_actions[game.board.state.fascist_track - 1]
            if action is None and game.board.state.fascist_track == 6:
                pass
            elif action == None:
                start_next_round(bot, game)
            elif action == "policy":
                bot.send_message(game.chat_id,
                                 "Presidential Power enabled: Policy Peek " + u"\U0001F52E" + "\nPresident %s now knows the next three policies on "
                                                                                              "the pile.  The President may share "
                                                                                              "(or lie about!) the results of their "
                                                                                              "investigation at their discretion." % game.board.state.president.name)
                action_policy(bot, game)
            elif action == "kill":
                bot.send_message(game.chat_id,
                                 "Presidential Power enabled: Execution " + u"\U0001F5E1" + "\nPresident %s has to kill one person. You can "
                                                                                            "discuss the decision now but the "
                                                                                            "President has the final say." % game.board.state.president.name)
                action_kill(bot, game)
            elif action == "inspect":
                bot.send_message(game.chat_id,
                                 "Presidential Power enabled: Investigate Loyalty " + u"\U0001F50E" + "\nPresident %s may see the party membership of one "
                                                                                                      "player. The President may share "
                                                                                                      "(or lie about!) the results of their "
                                                                                                      "investigation at their discretion." % game.board.state.president.name)
                action_inspect(bot, game)
            elif action == "choose":
                bot.send_message(game.chat_id,
                                 "Presidential Power enabled: Call Special Election " + u"\U0001F454" + "\nPresident %s gets to choose the next presidential "
                                                                                                        "candidate. Afterwards the order resumes "
                                                                                                        "back to normal." % game.board.state.president.name)
                action_choose(bot, game)
        else:
            start_next_round(bot, game)
    else:
        start_next_round(bot, game)

def choose_veto(bot, game, player_id, answer):
    print(f"choose_veto called with player_id: {player_id} and answer: {answer}")

    # Assuming you have a way to get player from player_id
    player = game.get_player(player_id)
    
    if answer == "yesveto":
        bot.send_message(game.chat_id,
                         f"{player.name} accepted the Veto. No policy was enacted but this counts as a failed election.")
        game.board.discards.extend(game.board.state.drawn_policies)
        game.board.state.drawn_policies = []
        game.board.state.failed_votes += 1
        if game.board.state.failed_votes == 3:
            do_anarchy(bot, game)

        else:
            # call print_board and start_next_round functions here
            pass  # Replace with the actual function calls
    elif answer == "noveto":
        game.board.state.veto_refused = True
        bot.send_message(game.chat_id,
                         f"{player.name} refused the Veto. The Chancellor now has to choose a policy!")
        # call pass_two_policies function here
        pass  # Replace with the actual function call
    else:
        print("choose_veto: Callback data can either be \"yesveto\" or \"noveto\".")

def do_anarchy(bot, game):
    print('do_anarchy called')
    bot.send_message(game.chat_id, game.board.print_board())
    bot.send_message(game.chat_id, "ANARCHY!!")
    game.board.state.president = None
    game.board.state.chancellor = None
    top_policy = game.board.policies.pop(0)
    game.board.state.last_votes = {}
    enact_policy(bot, game, top_policy, True)

def action_policy(bot, game):
    print('action_policy called')
    topPolicies = ""
    
    # shuffle discard pile with rest if rest < 3
    shuffle_policy_pile(bot, game)
    
    for policy in game.board.policies[:3]:  # This will take up to 3 items, but won't raise an error if there are less than 3
        topPolicies += policy + "\n"
    
    if not re.search('test', str(game.board.state.president.user_id)):
        bot.send_message(game.board.state.president.user_id,
                         "The top three polices are (top most first):\n%s\nYou may lie about this." % topPolicies)
    
    start_next_round(bot, game)

def bot_kill_player(bot, game, player_to_kill):
    print(f"kill_player called for player: {player_to_kill.name}")

    if player_to_kill.alive:

        # Remove player's vote if they have voted
        if player_to_kill.user_id in game.votes:
            del game.votes[player_to_kill.user_id]

        player_to_kill.alive = False
        if game.player_sequence.index(player_to_kill) <= game.board.state.player_counter:
            game.board.state.player_counter -= 1
        game.player_sequence.remove(player_to_kill)
        game.board.state.dead += 1
        print(f"President {game.board.state.president.name} killed {player_to_kill.name}")
        bot.send_message(game.chat_id, f"{game.board.state.president.name} killed {player_to_kill.name}!")
        
        if player_to_kill.role == "Hitler":
            bot.send_message(game.chat_id, f"President {game.board.state.president.name} killed {player_to_kill.name}. ")
            end_game(bot, game, 2)
        else:
            bot.send_message(game.chat_id, f"President {game.board.state.president.name} killed {player_to_kill.name} who was not Hitler. {player_to_kill.name}, you are dead now and are not allowed to talk anymore!")
            bot.send_message(game.chat_id, game.board.print_board())
            start_next_round(bot, game)
    else:
        print(f"{player_to_kill.name} is already dead!")

def action_kill(bot, game):
    print('action_kill called')
    btns = []
    for player in game.get_players():
        if player != game.board.state.president and player.alive == True:
            name = player.name
            btns.append([types.InlineKeyboardButton(name, callback_data=str(game.chat_id) + "_kill_" + str(player.user_id))])

    kill_markup = types.InlineKeyboardMarkup(btns)
    if not re.search('test', str(game.board.state.president.user_id)):
        bot.send_message(game.board.state.president.user_id, game.board.print_board())
        bot.send_message(game.board.state.president.user_id,
                        'You have to kill one person. You can discuss your decision with the others. Choose wisely!',
                        reply_markup=kill_markup)
    else:

            alive_players = [player for player in game.get_players() if player.alive == True and player != game.board.state.president]
            if alive_players:  # If there is at least one player to kill
                player_to_kill = random.choice(alive_players)  # Choose a random player
                bot_kill_player(bot, game, player_to_kill)

def bot_choose_next_president(bot, game):
    print('bot_choose_next_president called')
    alive_players = [player for player in game.get_players() if player.alive == True and player != game.board.state.president]
    if alive_players:  # If there is at least one player to choose
        chosen_president = random.choice(alive_players)  # Choose a random player
        print("BOT ASIGN PRESIDENT: ", chosen_president)
        game.board.state.chosen_president = chosen_president  # Assign the chosen player as the next president
        bot.send_message(game.chat_id, f"{game.board.state.president.name} chose {chosen_president.name} as the next presidential candidate!")
    else:
        print('No player available to choose as next president')

def action_choose(bot, game):
    print('action_choose called')
    strcid = str(game.chat_id)
    btns = []

    for player in game.get_players():
        if player != game.board.state.president and player.alive == True:
            name = player.name
            btns.append([types.InlineKeyboardButton(name, callback_data=strcid + "_choo_" + str(player.user_id))])

    inspectMarkup = types.InlineKeyboardMarkup(btns)
    if not re.search('test', str(game.board.state.president.user_id)):
        bot.send_message(game.board.state.president.user_id, game.board.print_board())
        bot.send_message(game.board.state.president.user_id,
                        'You get to choose the next presidential candidate. Afterwards the order resumes back to normal. Choose wisely!',
                        reply_markup=inspectMarkup)
    else:
        bot_choose_next_president(bot, game)

def bot_inspect_player(bot, game):
    print('bot_inspect_player called')
    alive_players = [player for player in game.get_players() if player.alive == True and player != game.board.state.president]
    if alive_players:  # If there is at least one player to inspect
        player_to_inspect = random.choice(alive_players)  # Choose a random player
        bot.send_message(game.chat_id, f"{game.board.state.president.name} inspected {player_to_inspect.name} and found out their party membership is {player_to_inspect.party_membership}!")
    else:
        print('No player available to inspect')

def action_inspect(bot, game):
    print('action_inspect called')
    strcid = str(game.chat_id)
    btns = []
    for player in game.get_players():
        if player != game.board.state.president and player.alive == True:
            name = player.name
            btns.append([types.InlineKeyboardButton(name, callback_data=strcid + "_insp_" + str(player.user_id))])

    inspectMarkup = types.InlineKeyboardMarkup(btns)
    if not re.search('test', str(game.board.state.president.user_id)):
        bot.send_message(game.board.state.president.user_id, game.board.print_board())
        bot.send_message(game.board.state.president.user_id,
                        'You may see the party membership of one player. Which do you want to know? Choose wisely!',
                        reply_markup=inspectMarkup)
    else:
        bot_inspect_player(bot, game)

def action_inspect(bot, game):
    print('action_inspect called')
    strcid = str(game.chat_id)
    btns = []
    for player in game.get_players():
        if player != game.board.state.president.user_id and player.alive == True:
            name = player.name
            btns.append([types.InlineKeyboardButton(name, callback_data=strcid + "_insp_" + str(player.user_id))])

    inspectMarkup = types.InlineKeyboardMarkup(btns)
    if not re.search('test', str(game.board.state.president.user_id)):
        bot.send_message(game.board.state.president.user_id, game.board.print_board())
        bot.send_message(game.board.state.president.user_id,
                        'You may see the party membership of one player. Which do you want to know? Choose wisely!',
                        reply_markup=inspectMarkup)

def start_next_round(bot, game):
    print('start_next_round called')
    print("saving game state with players: ")
    for p in game.get_players():
        print(p.name, p.role)
    GamesController.save_game_state(game.chat_id)
    if game.board.state.game_endcode == 0:
        time.sleep(8)
        if game.board.state.chosen_president is None:
            game.next_turn()
        start_round(bot, game)

##
#
# End of round
#
##

def end_game(bot, game, game_endcode):
    print('end_game called')
    ##
    # game_endcode:
    #   -2  fascists win by electing Blue as chancellor
    #   -1  fascists win with 6 fascist policies
    #   0   not ended
    #   1   liberals win with 5 liberal policies
    #   2   liberals win by killing Blue
    #   99  game cancelled
    #
   # with open(STATS, 'r') as f:
    #    stats = json.load(f)

    if game_endcode == 99:
        if game.board is not None:
            bot.send_message(game.chat_id,
                             "Game cancelled!\n\n%s" % game.print_roles())
            # bot.send_message(ADMIN, "Game of Secret Hitler canceled in group %d" % game.cid)
           # stats['cancelled'] = stats['cancelled'] + 1
        else:
            bot.send_message(game.chat_id, "Game cancelled!")
    else:
        if game_endcode == -2:
            bot.send_message(game.chat_id,
                             "Game over! The fascists win by electing Hitler as Chancellor!\n\n%s" % game.print_roles())
            #stats['fascwin_blue'] = stats['fascwin_blue'] + 1
        if game_endcode == -1:
            bot.send_message(game.chat_id,
                             "Game over! The fascists win by enacting 6 fascist policies!\n\n%s" % game.print_roles())
            #stats['fascwin_policies'] = stats['fascwin_policies'] + 1
        if game_endcode == 1:
            bot.send_message(game.chat_id,
                             "Game over! The liberals win by enacting 5 liberal policies!\n\n%s" % game.print_roles())
            #stats['libwin_policies'] = stats['libwin_policies'] + 1
        if game_endcode == 2:
            bot.send_message(game.chat_id,
                             "Game over! The liberals win by killing Hitler!\n\n%s" % game.print_roles())
            #stats['libwin_kill'] = stats['libwin_kill'] + 1
    print("deleting at end game")
    del GamesController.games[game.chat_id]

            # bot.send_message(ADMIN, "Game of Secret Blue ended in group %d" % game.cid)


def get_membership(role):
    print('get_membership called')
    if role == "Fascist" or role == "Hitler":
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
                bot.send_message(player.user_id, "Hitler is: %s" % hitler.name)
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
    # log.info('shuffle_policy_pile called')
    if len(game.board.policies) < 3:
        game.board.discards.extend(game.board.policies)  # Combining the remaining policies with the discards
        random.shuffle(game.board.discards)  # Shuffle the combined pile
        game.board.policies = game.board.discards  # Assign the shuffled deck to policies
        game.board.discards = []  # Reset the discard pile

        if not game.board.policies:  # If both discard and policies piles are empty, handle this edge case
            bot.send_message(game.chat_id, "There are no policies left!")
            return  # Add necessary handling here for when there are no policies left

        bot.send_message(game.chat_id,
                         "There were not enough cards left on the policy pile so I shuffled the rest with the discard pile!")