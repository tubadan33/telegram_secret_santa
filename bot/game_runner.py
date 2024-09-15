from constants.Cards import playerSets
from gamecontroller import GamesController
from random import randrange
from telebot import types
import random
import datetime
import time
import re
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()


def start_round(bot, game):
    print("start_round called")
    print("Debug Info:")
    print("game turn:", game.turn)
    print("Chosen: ", game.board.state.chosen_president)
    print("nominated_president:", game.board.state.nominated_president)
    print("Type of nominated_president:", type(game.board.state.nominated_president))

    # If the turn isn't initialized, set it to 0
    if game.turn is None:
        game.turn = 0
        game.board.state.nominated_president = game.player_sequence[game.turn]

    elif game.board.state.chosen_president:
        # Update the nominated president and reset the chosen president
        game.board.state.nominated_president = game.board.state.chosen_president
        game.board.state.chosen_president = None
    else:
        # If no special president, revert back to the saved index if it exists and then advance the turn
        if (
            hasattr(game.board.state, "chosen_president_index")
            and game.board.state.chosen_president_index is not None
        ):
            game.turn = game.board.state.chosen_president_index
            game.board.state.chosen_president_index = None  # reset the saved index
        # Now advance the turn in normal sequence
        game.turn = (game.turn + 1) % len(game.player_sequence)
        game.board.state.nominated_president = game.player_sequence[game.turn]

    # Send message about the nominated president
    bot.send_message(
        game.chat_id,
        "The next presidential candidate is %s.\n%s, please nominate a Chancellor in our private chat!"
        % (
            game.board.state.nominated_president.name,
            game.board.state.nominated_president.name,
        ),
    )
    print("Round Starting, nom pres ", game.board.state.nominated_president)

    choose_chancellor(bot, game)


def choose_chancellor(bot, game):
    print("choose_chancellor called")

    # Add this check at the beginning of your function
    if (
        game.player_sequence[game.turn].user_id
        != game.board.state.nominated_president.user_id
    ):
        print(
            "It is not the turn of",
            game.board.state.nominated_president.name,
            "to nominate a chancellor",
        )
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
            if (
                player.user_id != game.board.state.nominated_president.user_id
                and player.alive == True
                and player.user_id != pres_player
                and player.user_id != chan_player
            ):
                btns.append(
                    [
                        types.InlineKeyboardButton(
                            player.name,
                            callback_data=strcid
                            + "_choose_chancellor_"
                            + str(player.user_id),
                        )
                    ]
                )
        else:
            if (
                player.user_id != game.board.state.nominated_president.user_id
                and player.alive == True
                and player.user_id != chan_player
            ):
                btns.append(
                    [
                        types.InlineKeyboardButton(
                            player.name,
                            callback_data=strcid
                            + "_choose_chancellor_"
                            + str(player.user_id),
                        )
                    ]
                )

    chancellorMarkup = types.InlineKeyboardMarkup(btns)
    print(str(game.board.state.nominated_president.user_id))
    bot.send_message(
        game.board.state.nominated_president.user_id, game.board.print_board()
    )
    bot.send_message(
        game.board.state.nominated_president.user_id,
        "Please nominate your chancellor!",
        reply_markup=chancellorMarkup,
    )


def nominate_chosen_chancellor(bot, game):
    print(
        "President %s (%s) nominated %s (%s)"
        % (
            game.board.state.nominated_president.name,
            game.board.state.nominated_president.user_id,
            game.board.state.nominated_chancellor.name,
            game.board.state.nominated_chancellor.user_id,
        )
    )
    bot.send_message(
        game.chat_id,
        "President %s nominated %s as Chancellor. Please vote now!"
        % (
            game.board.state.nominated_president.name,
            game.board.state.nominated_chancellor.name,
        ),
    )

    vote(bot, game)


def vote(bot, game):
    print("vote called")

    game.dateinitvote = datetime.datetime.now()
    strcid = str(game.chat_id)

    for player in game.get_players_alive():
        # Create vote buttons for this specific player
        btns = [
            [
                types.InlineKeyboardButton(
                    "Ja", callback_data=f"{strcid}_vote_{player.user_id}_Ja"
                )
            ],
            [
                types.InlineKeyboardButton(
                    "Nein", callback_data=f"{strcid}_vote_{player.user_id}_Nein"
                )
            ],
        ]
        voteMarkup = types.InlineKeyboardMarkup(btns)

        bot.send_message(player.user_id, game.board.print_board())
        vote_message = bot.send_message(
            player.user_id,
            "Do you want to elect President %s and Chancellor %s?"
            % (
                game.board.state.nominated_president.name,
                game.board.state.nominated_chancellor.name,
            ),
            reply_markup=voteMarkup,
        )
        print("MESSAGE ID: ", vote_message.message_id)
        game.vote_messages[player.user_id] = vote_message.message_id


def check_and_count_votes(bot, game):
    print("check_and_count_votes called")
    print(f"Current votes: {game.votes}")
    print(f"Total number of players: {len(game.get_players())}")
    print(f"Number of votes needed for counting: {len(game.get_players_alive())}")

    if len(game.votes) == len(game.get_players_alive()):
        print("All votes have been collected, proceeding to count votes")
        count_votes(bot, game)
    else:
        print("Not all votes have been collected yet")


def count_votes(bot, game):
    print("count_votes called")
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
            game.board.state.nominated_president.name,
            game.board.state.nominated_chancellor.name,
        )
        game.board.state.chancellor = game.board.state.nominated_chancellor
        game.board.state.president = game.board.state.nominated_president
        game.board.state.nominated_president = None
        game.board.state.nominated_chancellor = None
        bot.send_message(
            game.chat_id, voting_text
        )  # Send the message before setting to None
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
    print("voting_aftermath called")
    game.board.state.last_votes = {}
    game.clear_user_timers()
    game.votes.clear()
    if voting_success:
        if (
            game.board.state.naughtist_track >= 3
            and game.board.state.chancellor.role == "Santa"
        ):
            # naughtists win, because Santa was elected as chancellor after 3 naughtist policies
            game.board.state.game_endcode = -2
            end_game(bot, game, game.board.state.game_endcode)
        elif (
            game.board.state.naughtist_track >= 3
            and game.board.state.chancellor.role != "Santa"
            and game.board.state.chancellor not in game.board.state.not_santas
        ):
            game.board.state.not_santas.append(game.board.state.chancellor)
            draw_policies(bot, game)
        else:
            # voting was successful and Santa was not nominated as chancellor after 3 naughtist policies
            draw_policies(bot, game)
    else:
        bot.send_message(game.chat_id, game.board.print_board())
        GamesController.save_game_state(game.chat_id)
        start_next_round(
            bot, game
        )  # Start a new round directly instead of calling start_next_round


def draw_policies(bot, game):
    print("draw_policies called")
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
        btns.append(
            [types.InlineKeyboardButton(policy, callback_data=strcid + "_" + policy)]
        )

    choosePolicyMarkup = types.InlineKeyboardMarkup(btns)

    # Handle user or bot drawing policies
    bot.send_message(
        game.board.state.president.user_id,
        "You drew the following 3 policies. Which one do you want to discard?",
        reply_markup=choosePolicyMarkup,
    )


def pass_two_policies(bot, game):
    print("pass_two_policies called")
    strcid = str(game.chat_id)
    btns = []
    for policy in game.board.state.drawn_policies:
        btns.append(
            [types.InlineKeyboardButton(policy, callback_data=strcid + "_" + policy)]
        )
    choosePolicyMarkup = types.InlineKeyboardMarkup(btns)

    if len(game.board.state.drawn_policies) != 2:
        print(
            f"Error: expected 2 policies but got {len(game.board.state.drawn_policies)}"
        )

    if game.board.state.naughtist_track == 5 and not game.board.state.veto_refused:
        btns.append(
            [types.InlineKeyboardButton("Veto", callback_data=strcid + "_veto")]
        )
        bot.send_message(
            game.chat_id,
            "President %s gave two policies to Chancellor %s."
            % (game.board.state.president.name, game.board.state.chancellor.name),
        )
        bot.send_message(
            game.board.state.chancellor.user_id,
            "President %s gave you the following 2 policies. Which one do you want to enact? You can also use your Veto power."
            % game.board.state.president.name,
            reply_markup=choosePolicyMarkup,
        )

    elif game.board.state.veto_refused:
        bot.send_message(
            game.board.state.chancellor.user_id,
            "President %s refused your Veto. Now you have to choose. Which one do you want to enact?"
            % game.board.state.president.name,
            reply_markup=choosePolicyMarkup,
        )

    elif game.board.state.naughtist_track < 5:
        bot.send_message(
            game.board.state.chancellor.user_id,
            "President %s gave you the following 2 policies. Which one do you want to enact?"
            % game.board.state.president.name,
            reply_markup=choosePolicyMarkup,
        )


def enact_policy(bot, game, policy, anarchy):
    print("enact_policy called")

    if policy == "niceist":
        game.board.state.niceist_track += 1
    elif policy == "naughtist":
        game.board.state.naughtist_track += 1

    game.board.state.failed_votes = 0  # reset counter

    if not anarchy:
        bot.send_message(
            game.chat_id,
            "President %s and Chancellor %s enacted a %s policy!"
            % (
                game.board.state.president.name,
                game.board.state.chancellor.name,
                policy,
            ),
        )
    else:
        bot.send_message(game.chat_id, "The top most policy was enacted: %s" % policy)

    time.sleep(3)
    bot.send_message(game.chat_id, game.board.print_board())
    # end of round
    if game.board.state.niceist_track == 5:
        game.board.state.game_endcode = 1
        end_game(
            bot, game, game.board.state.game_endcode
        )  # niceists win with 5 niceist policies
    if game.board.state.naughtist_track == 6:
        game.board.state.game_endcode = -1
        end_game(
            bot, game, game.board.state.game_endcode
        )  # naughtists win with 6 naughtist policies

    time.sleep(3)
    # End of legislative session, shuffle if necessary
    shuffle_policy_pile(bot, game)

    if not anarchy:
        if policy == "naughtist":
            action = game.board.naughtist_track_actions[
                game.board.state.naughtist_track - 1
            ]
            if action is None and game.board.state.naughtist_track == 6:
                pass
            elif action == None:
                GamesController.save_game_state(game.chat_id)
                start_next_round(bot, game)
            elif action == "policy":
                bot.send_message(
                    game.chat_id,
                    "Presidential Power enabled: Policy Peek "
                    + "\U0001f52e"
                    + "\nPresident %s now knows the next three policies on "
                    "the pile.  The President may share "
                    "(or lie about!) the results of their "
                    "investigation at their discretion."
                    % game.board.state.president.name,
                )
                action_policy(bot, game)
            elif action == "kill":
                bot.send_message(
                    game.chat_id,
                    "Presidential Power enabled: Execution "
                    + "\U0001f5e1"
                    + "\nPresident %s has to kill one person. You can "
                    "discuss the decision now but the "
                    "President has the final say." % game.board.state.president.name,
                )
                action_kill(bot, game)
            elif action == "inspect":
                bot.send_message(
                    game.chat_id,
                    "Presidential Power enabled: Investigate Loyalty "
                    + "\U0001f50e"
                    + "\nPresident %s may see the party membership of one "
                    "player. The President may share "
                    "(or lie about!) the results of their "
                    "investigation at their discretion."
                    % game.board.state.president.name,
                )
                action_inspect(bot, game)
            elif action == "choose":
                bot.send_message(
                    game.chat_id,
                    "Presidential Power enabled: Call Special Election "
                    + "\U0001f454"
                    + "\nPresident %s gets to choose the next presidential "
                    "candidate. Afterwards the order resumes "
                    "back to normal." % game.board.state.president.name,
                )
                action_choose(bot, game)
        else:
            GamesController.save_game_state(game.chat_id)
            start_next_round(bot, game)
    else:
        GamesController.save_game_state(game.chat_id)
        start_next_round(bot, game)


def choose_veto(bot, game, player_id, answer):
    print(f"choose_veto called with player_id: {player_id} and answer: {answer}")

    # Assuming you have a way to get player from player_id
    player = game.get_player(player_id)

    if answer == "yesveto":
        bot.send_message(
            game.chat_id,
            f"{player.name} accepted the Veto. No policy was enacted but this counts as a failed election.",
        )
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
        bot.send_message(
            game.chat_id,
            f"{player.name} refused the Veto. The Chancellor now has to choose a policy!",
        )
        # call pass_two_policies function here
        pass  # Replace with the actual function call
    else:
        print('choose_veto: Callback data can either be "yesveto" or "noveto".')


def do_anarchy(bot, game):
    print("do_anarchy called")
    shuffle_policy_pile(bot, game)
    bot.send_message(game.chat_id, game.board.print_board())
    bot.send_message(game.chat_id, "ANARCHY!!")
    game.board.state.president = None
    game.board.state.chancellor = None
    top_policy = game.board.policies.pop(0)
    game.board.state.last_votes = {}
    enact_policy(bot, game, top_policy, True)


def action_policy(bot, game):
    print("action_policy called")
    topPolicies = ""

    # shuffle discard pile with rest if rest < 3
    shuffle_policy_pile(bot, game)

    for policy in game.board.policies[
        :3
    ]:  # This will take up to 3 items, but won't raise an error if there are less than 3
        topPolicies += policy + "\n"

    bot.send_message(
        game.board.state.president.user_id,
        "The top three polices are (top most first):\n%s\nYou may lie about this."
        % topPolicies,
    )
    GamesController.save_game_state(game.chat_id)
    start_next_round(bot, game)


def action_kill(bot, game):
    print("action_kill called")
    btns = []
    for player in game.get_players():
        if player.alive == True:
            name = player.name
            btns.append(
                [
                    types.InlineKeyboardButton(
                        name,
                        callback_data=str(game.chat_id)
                        + "_kill_"
                        + str(player.user_id),
                    )
                ]
            )

    kill_markup = types.InlineKeyboardMarkup(btns)
    bot.send_message(game.board.state.president.user_id, game.board.print_board())
    bot.send_message(
        game.board.state.president.user_id,
        "You have to kill one person. You can discuss your decision with the others. Choose wisely!",
        reply_markup=kill_markup,
    )


def action_choose(bot, game):
    print("action_choose called")
    strcid = str(game.chat_id)
    btns = []

    for player in game.get_players():
        if player != game.board.state.president and player.alive == True:
            name = player.name
            btns.append(
                [
                    types.InlineKeyboardButton(
                        name, callback_data=strcid + "_choo_" + str(player.user_id)
                    )
                ]
            )

    inspectMarkup = types.InlineKeyboardMarkup(btns)
    bot.send_message(game.board.state.president.user_id, game.board.print_board())
    bot.send_message(
        game.board.state.president.user_id,
        "You get to choose the next presidential candidate. Afterwards the order resumes back to normal. Choose wisely!",
        reply_markup=inspectMarkup,
    )


def action_inspect(bot, game):
    print("action_inspect called")
    strcid = str(game.chat_id)
    btns = []
    for player in game.get_players():
        if player != game.board.state.president and player.alive == True:
            name = player.name
            btns.append(
                [
                    types.InlineKeyboardButton(
                        name, callback_data=strcid + "_insp_" + str(player.user_id)
                    )
                ]
            )

    inspectMarkup = types.InlineKeyboardMarkup(btns)
    bot.send_message(game.board.state.president.user_id, game.board.print_board())
    bot.send_message(
        game.board.state.president.user_id,
        "You may see the party membership of one player. Which do you want to know? Choose wisely!",
        reply_markup=inspectMarkup,
    )


def start_next_round(bot, game):
    if game.board.state.game_endcode == 0:
        time.sleep(8)

        if game.board.state.chosen_president is not None:
            game.turn = game.board.state.chosen_president_index
            # Clear the chosen_president_index after using it
            del game.board.state.chosen_president_index
        else:
            game.next_turn()

        start_round(bot, game)


##
#
# End of round
#
##


def end_game(bot, game, game_endcode):
    print("end_game called")
    ##
    # game_endcode:
    #   -2  naughtists win by electing Blue as chancellor
    #   -1  naughtists win with 6 naughtist policies
    #   0   not ended
    #   1   niceists win with 5 niceist policies
    #   2   niceists win by killing Blue
    #   99  game cancelled
    #
    # with open(STATS, 'r') as f:
    #    stats = json.load(f)

    if game_endcode == 99:
        if game.board is not None:
            bot.send_message(game.chat_id, "Game cancelled!\n\n%s" % game.print_roles())
            # bot.send_message(ADMIN, "Game of Secret Santa canceled in group %d" % game.cid)
        # stats['cancelled'] = stats['cancelled'] + 1
        else:
            bot.send_message(game.chat_id, "Game cancelled!")
    else:
        if game_endcode == -2:
            bot.send_message(
                game.chat_id,
                "Game over! The naughtists win by electing Santa as Chancellor!\n\n%s"
                % game.print_roles(),
            )
            # stats['fascwin_blue'] = stats['fascwin_blue'] + 1
        if game_endcode == -1:
            bot.send_message(
                game.chat_id,
                "Game over! The naughtists win by enacting 6 naughtist policies!\n\n%s"
                % game.print_roles(),
            )
            # stats['fascwin_policies'] = stats['fascwin_policies'] + 1
        if game_endcode == 1:
            bot.send_message(
                game.chat_id,
                "Game over! The niceists win by enacting 5 niceist policies!\n\n%s"
                % game.print_roles(),
            )
            # stats['libwin_policies'] = stats['libwin_policies'] + 1
        if game_endcode == 2:
            bot.send_message(
                game.chat_id,
                "Game over! The niceists win by killing Santa!\n\n%s"
                % game.print_roles(),
            )
            # stats['libwin_kill'] = stats['libwin_kill'] + 1
    print("deleting at end game")
    del GamesController.games[game.chat_id]

    # bot.send_message(ADMIN, "Game of Secret Blue ended in group %d" % game.cid)


def get_membership(role):
    print("get_membership called")
    if role == "Naughtist" or role == "Santa":
        return "naughtist"
    elif role == "Niceist":
        return "niceist"
    else:
        return None


def print_player_info(player_number):
    if player_number == 5:
        return "There are 3 Niceists, 1 Naughtist and Santa. Santa knows who the Naughtist is."
    elif player_number == 6:
        return "There are 4 Niceists, 1 Naughtist and Santa. Santa knows who the Naughtist is."
    elif player_number == 7:
        return "There are 4 Niceists, 2 Naughtist and Santa. Santa doesn't know who the Naughtists are."
    elif player_number == 8:
        return "There are 5 Niceists, 2 Naughtist and Santa. Santa doesn't know who the Naughtists are."
    elif player_number == 9:
        return "There are 5 Niceists, 3 Naughtist and Santa. Santa doesn't know who the Naughtists are."
    elif player_number == 10:
        return "There are 6 Niceists, 3 Naughtist and Santa. Santa doesn't know who the Naughtists are."


def inform_players(bot, game):
    player_number = len(game.get_players())
    available_roles = list(playerSets[player_number]["roles"])
    print(", ".join(str(player.user_id) for player in game.get_players()))

    for player in game.get_players():
        random_index = randrange(len(available_roles))
        role = available_roles.pop(random_index)
        player.role = role
        player.party = get_membership(role)

        bot.send_message(
            player.user_id,
            "Your secret role is: %s\nYour party membership is: %s"
            % (role, get_membership(role)),
        )

    bot.send_message(
        game.chat_id,
        "Let's start the game with %d players!\n%s\nCheck your private messages for your secret role!"
        % (player_number, print_player_info(player_number)),
    )


def inform_naughtists(bot, game):
    player_number = len(game.get_players())

    for player in game.get_players():
        role = player.role
        print("ROLE: ", role)
        if role == "Naughtist":
            naughtists = [
                p
                for p in game.get_players()
                if p.role == "Naughtist" and p.user_id != player.user_id
            ]
            santa = next(p for p in game.get_players() if p.role == "Santa")
            if player_number > 6:
                fstring = ", ".join([f.name for f in naughtists])
                bot.send_message(
                    player.user_id, "Your fellow naughtists are: %s" % fstring
                )
            bot.send_message(player.user_id, "Santa is: %s" % santa.name)
        elif role == "Santa":
            if player_number <= 6:
                naughtist = next(p for p in game.get_players() if p.role == "Naughtist")
        elif role == "Niceist":
            pass
        else:
            print("inform_naughtists: can't handle the role %s" % role)


def increment_player_counter(game):
    # log.info('increment_player_counter called')
    if game.board.state.player_counter < len(game.player_sequence) - 1:
        game.board.state.player_counter += 1
    else:
        game.board.state.player_counter = 0


def shuffle_policy_pile(bot, game):
    # log.info('shuffle_policy_pile called')
    print("DISCARDS: ", game.board.discards)
    print("POLICIES: ", game.board.policies)
    print("Shuffle policies called with: ", game.board.policies)
    if len(game.board.policies) < 3:
        print("DISCARDS: ", game.board.discards)
        print("POLICIES: ", game.board.policies)
        game.board.discards.extend(
            game.board.policies
        )  # Combining the remaining policies with the discards
        random.shuffle(game.board.discards)  # Shuffle the combined pile
        game.board.policies = (
            game.board.discards
        )  # Assign the shuffled deck to policies
        game.board.discards = []  # Reset the discard pile

        if (
            not game.board.policies
        ):  # If both discard and policies piles are empty, handle this edge case
            bot.send_message(game.chat_id, "There are no policies left!")
            game.board.policies = game.board.reset_policies(game.board.policies)

        bot.send_message(
            game.chat_id,
            "There were not enough cards left on the policy pile so I shuffled the rest with the discard pile!",
        )
