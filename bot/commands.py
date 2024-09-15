import datetime
import os
import re

import telebot
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv, dotenv_values

import game_runner
from game.game_functions import SecretSantaGame
from gamecontroller import GamesController

load_dotenv()

env = {
    **dotenv_values(),
    **os.environ
}

TELEGRAM_BOT_TOKEN = env.get("TELEGRAM_BOT_TOKEN")
USER_ADMIN_ID = env.get("USER_ADMIN_ID")
DEBUG_MODE = env.get("DEBUG_MODE", "false").lower() == "true"

if TELEGRAM_BOT_TOKEN is None:
    raise RuntimeError()


bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
scheduler = BackgroundScheduler()
scheduler.start()
bot.set_webhook()


commands = [  # command description used in the "help" command
    "/help - Gives you information about the available commands",
    "/start - Gives you a short piece of information about Secret Santa",
    "/symbols - Shows you all possible symbols of the board",
    "/newgame - Creates a new game",
    "/join - Joins an existing game",
    "/startgame - Starts an existing game when all players have joined",
    "/cancelgame - Cancels an existing game. All data of the game will be lost",
    "/board - Prints the current board with naughtist and niceists tracks, presidential order and election counter",
    "/calltovote - Calls the players to vote",
    "/ping - Ping",
]

symbols = [
    "\u25fb\ufe0f" + " Empty field without special power",
    "\u2716\ufe0f" + " Field covered with a card",  # X
    "\U0001f52e" + " Presidential Power: Policy Peek",  # crystal
    "\U0001f50e" + " Presidential Power: Investigate Loyalty",  # inspection glass
    "\U0001f5e1" + " Presidential Power: Execution",  # knife
    "\U0001f454" + " Presidential Power: Call Special Election",  # tie
    "\U0001f54a" + " niceists win",  # dove
    "\u2620" + " naughtists win",  # skull
]


@bot.callback_query_handler(
    func=lambda call: re.match(r"-?\w+_choose_chancellor_.*", call.data)
)
def callback_choose_chancellor(call):
    print(f"USER SELECTED CHANCELLOR: {call.data}")
    strcid, _, chosen_uid = call.data.partition("_choose_chancellor_")
    print(f"Checking player with user_id: {chosen_uid}")
    chat_id = int(strcid)
    print(f"Attempting to get game with chat_id: {chat_id}")
    game = GamesController.get_game(chat_id)
    if game is None:
        print(f"No game found with chat_id: {chat_id}")
        return
    print(f"Game found with chat_id: {chat_id}")
    if call.from_user.id != game.player_sequence[game.turn].user_id:
        bot.answer_callback_query(
            call.id,
            text="It is not your turn to nominate a chancellor",
            show_alert=True,
        )
        return
    if game.board is None:
        print("Game's board is None!")
        return
    print("Game's board is not None, proceeding to nominate_chosen_chancellor")
    chosen_chancellor = None
    chosen_chancellor = next(
        (p for p in game.get_players() if p.user_id == int(chosen_uid)), None
    )
    if chosen_chancellor is None:
        bot.answer_callback_query(call.id, text="Unknown player", show_alert=True)
        print("CHANCELLOR ERROR:", chosen_chancellor)
        return
    print("CHOSEN CHANCELLOR: ", chosen_chancellor.name)
    game.board.state.nominated_chancellor = chosen_chancellor
    # Call the next stage function
    game_runner.nominate_chosen_chancellor(bot, game)

    # Edit the message for the nominator
    bot.edit_message_text(
        "You nominated %s as Chancellor!" % game.board.state.nominated_chancellor.name,
        call.message.chat.id,
        call.message.message_id,
    )


@bot.callback_query_handler(
    func=lambda call: re.match(r"-?\d+_vote_\d+_(Ja|Nein)", call.data)
)
def callback_vote(call):
    if call.message:
        print(f"USER callback_vote called with data: {call.data}")

        strcid, _, uid_and_vote = call.data.partition("_vote_")
        uid, _, vote = uid_and_vote.partition("_")
        chat_id = int(strcid)
        uid = int(uid)
        game = GamesController.get_game(chat_id)
        if game is None:
            bot.answer_callback_query(call.id, text="Game not found", show_alert=True)
            return
        if uid not in game.votes:
            game.votes[uid] = vote
            if game.board.state.nominated_president is None:
                print("Nominated president is None!")
                return

            if game.board.state.nominated_chancellor is None:
                print("Nominated chancellor is None!")
                return
            bot.edit_message_text(
                "Thank you for your vote: %s to a President %s and a Chancellor %s"
                % (
                    vote,
                    game.board.state.nominated_president.name,
                    game.board.state.nominated_chancellor.name,
                ),
                uid,
                call.message.message_id,
            )

        else:
            bot.answer_callback_query(
                call.id, text="You already voted", show_alert=True
            )


@bot.callback_query_handler(
    func=lambda call: re.match(r"-?\d+_(naughtist|niceist)$", call.data)
)
def choose_policy(call):
    print(f"choose_policy called with data: {call.data}")

    strcid, _, answer = call.data.partition("_")
    chat_id = int(strcid)

    # Get the game instance
    game = GamesController.get_game(chat_id)

    if len(game.board.state.drawn_policies) == 3:
        # remove policy from drawn cards and add to discard pile, pass the other two policies
        discard_policy_index = None
        for i in range(3):
            if game.board.state.drawn_policies[i] == answer:
                discard_policy_index = i
                break
        if discard_policy_index is not None:
            game.board.discards.append(
                game.board.state.drawn_policies.pop(discard_policy_index)
            )
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id, message_id=call.message.message_id
        )
        game_runner.pass_two_policies(bot, game)
    elif len(game.board.state.drawn_policies) == 2:
        if answer == "veto":
            # handle the veto request
            game_runner.choose_veto(bot, game, call.from_user.id, answer)
        else:
            # remove policy from drawn cards and enact, discard the other card
            for i in range(2):
                if game.board.state.drawn_policies[i] == answer:
                    game.board.state.drawn_policies.pop(i)
                    break
            game.board.discards.append(game.board.state.drawn_policies.pop(0))
            assert len(game.board.state.drawn_policies) == 0
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id, message_id=call.message.message_id
            )
            game_runner.enact_policy(bot, game, answer, False)
    else:
        print(
            f"choose_policy: drawn_policies should be 3 or 2, but was {len(game.board.state.drawn_policies)}"
        )


@bot.callback_query_handler(func=lambda call: re.match(r"-?\w+_kill_\w+$", call.data))
def choose_kill(call):
    print(f"choose_kill called with data: {call.data}")

    strcid, _, answer = call.data.partition("_kill_")
    chat_id = int(strcid)
    player_to_kill_id = int(answer)

    game = GamesController.get_game(chat_id)

    player_to_kill = None
    for player in game.player_sequence:
        print(player, player.user_id)
        if player.user_id == player_to_kill_id:
            player_to_kill = player
            break

    if not player_to_kill:
        print(f"choose_kill: Player {player_to_kill_id} not found in game {chat_id}")
        return

    player_to_kill.alive = False
    if game.player_sequence.index(player_to_kill) <= game.board.state.player_counter:
        game.board.state.player_counter -= 1
    game.player_sequence.remove(player_to_kill)
    game.board.state.dead += 1
    print(
        f"Player {call.from_user.first_name} ({call.from_user.id}) killed {player_to_kill.name} ({player_to_kill.user_id})"
    )
    new_markup = telebot.types.InlineKeyboardMarkup()
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"You killed {player_to_kill.name}!",
        reply_markup=new_markup,
    )

    if player_to_kill.role == "Santa":
        bot.send_message(
            chat_id,
            f"President {game.board.state.president.name} killed {player_to_kill.name}. ",
        )
        game_runner.end_game(bot, game, 2)
    else:
        bot.send_message(
            chat_id,
            f"President {game.board.state.president.name} killed {player_to_kill.name} who was not Santa. {player_to_kill.name}, you are dead now and are not allowed to talk anymore!",
        )
        bot.send_message(chat_id, game.board.print_board())
        GamesController.save_game_state(game.chat_id)
        game_runner.start_next_round(bot, game)


@bot.callback_query_handler(func=lambda call: re.match(r"-?\w+_choo_\w+$", call.data))
def choose_choose(call):
    print(f"choose_choose called with data: {call.data}")

    strcid, _, struid = call.data.partition("_choo_")
    chat_id = int(strcid)
    chosen_user_id = int(struid)
    # Get the game instance
    game = GamesController.get_game(chat_id)
    chosen_player = next(
        (player for player in game.player_sequence if player.user_id == chosen_user_id),
        None,
    )
    if chosen_player is None:
        print(f"choose_choose: Player with user_id {chosen_user_id} not found")
        return

    # Save the chosen president and save the original turn index
    game.board.state.chosen_president = chosen_player
    game.board.state.chosen_president_index = game.turn

    # Update the turn to reflect the chosen president's position in the sequence
    game.turn = game.player_sequence.index(chosen_player)

    # Inform the players and start the next round
    bot.send_message(
        call.from_user.id, f"You chose {chosen_player.name} as the next president!"
    )
    bot.send_message(
        game.chat_id,
        f"President {game.board.state.president.name} chose {chosen_player.name} as the next president.",
    )
    GamesController.save_game_state(game.chat_id)
    game_runner.start_next_round(bot, game)


@bot.callback_query_handler(func=lambda call: re.match(r"-?\w+_insp_\w+$", call.data))
def choose_inspect(call):
    print("choose_inspect called")
    strcid, _, answer = call.data.partition("_insp_")
    chat_id = int(strcid)
    game = GamesController.get_game(chat_id)
    chosen = next(
        (player for player in game.player_sequence if str(player.user_id) == answer),
        None,
    )
    if chosen is not None:
        print(
            f"Player {call.from_user.first_name} ({call.from_user.id}) inspects {chosen.name} ({chosen.user_id})'s party membership ({chosen.party})"
        )

        new_markup = telebot.types.InlineKeyboardMarkup()
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"The party membership of {chosen.name} is {chosen.party}",
            reply_markup=new_markup,
        )

        bot.send_message(
            game.chat_id,
            f"President {game.board.state.president.name} inspected {chosen.name}.",
        )
        GamesController.save_game_state(game.chat_id)
        game_runner.start_next_round(bot, game)
    else:
        print("choose_inspect: The chosen player was not found in the game!")


@bot.callback_query_handler(func=lambda call: True)
def callback_catchall(call):
    print(f"Catch-all handler received data: {call.data}")


@bot.message_handler(commands=["help"])
def help(message):
    chat_id = message.chat.id
    help_text = "The following commands are available:\n"
    for i in commands:
        help_text += i + "\n"
    bot.send_message(chat_id, help_text)


@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    bot.send_message(
        chat_id,
        '"Secret Santa is a social deduction game for 5-10 people about finding and stopping the Secret Santa.'
        " The majority of players are niceists. If they can learn to trust each other, they have enough "
        "votes to control the table and win the game. But some players are naughtists. They will say whatever "
        "it takes to get elected, enact their agenda, and blame others for the fallout. The niceists must "
        "work together to discover the truth before the naughtists install their cold-blooded leader and win "
        'the game."\n- official description of Secret Santa\n\nAdd me to a group and type /newgame to create a game!',
    )


@bot.message_handler(commands=["restart"])
def load_crashed_game(message):
    chat_id = message.chat.id
    game = GamesController.get_game(chat_id)
    print(game.get_game_phase())
    if game.get_game_phase() != "waiting_for_players":
        bot.send_message(chat_id, "Game has started, cannot load prior game instance.")
    else:
        with open("state_save/game_state.pkl", "rb") as file:
            GamesController.load_game_state(chat_id)
            game = GamesController.get_game(chat_id)
            try:
                print(game.game_phase)
            except:
                print("couldnt print game state")
            bot.send_message(chat_id, "Setting up prior game state...")
            game_runner.start_next_round(bot, game)


@bot.message_handler(commands=["newgame"])
def newgame(message):
    chat_id = message.chat.id
    game = GamesController.get_game(chat_id)
    groupType = message.chat.type
    if groupType not in ["group", "supergroup"]:
        bot.send_message(
            chat_id, "You have to add me to a group first and type /newgame there!"
        )
    elif game:
        bot.send_message(
            chat_id,
            "There is currently a game running. If you want to end it please type /cancelgame!",
        )
    else:
        new_game = SecretSantaGame(
            chat_id, message.from_user.id
        )  # 0 as a placeholder for player_count, it will be replaced when the game starts.
        GamesController.new_game(chat_id, new_game)
        bot.send_message(
            chat_id,
            "New game created! Each player has to /join the game.\nThe initiator of this game (or the admin) can /join too and type /startgame when everyone has joined the game!",
        )


@bot.message_handler(commands=["startgame"])
def start_game(message):
    chat_id = message.chat.id
    game = GamesController.get_game(chat_id)
    if game is None:
        bot.send_message(
            chat_id, "There is no game in this chat. Create a new game with /newgame"
        )
    elif game.game_phase == "game_started":
        bot.send_message(chat_id, "The game is already running!")
        # and not is_admin(message.from_user.id, chat_id)
    elif message.from_user.id != game.initiator_id and bot.get_chat_member(
        chat_id, message.from_user.id
    ).status not in ("administrator", "creator"):
        bot.send_message(
            chat_id,
            "Only the initiator of the game or a group admin can start the game with /startgame",
        )
    else:
        start_message = game.start_game(bot, game)
        bot.send_message(chat_id, start_message)


@bot.message_handler(commands=["join"])
def join(message, user=None, name=None):
    print(user, name)
    group_name = message.chat.title
    chat_id = message.chat.id
    groupType = message.chat.type
    game = GamesController.get_game(chat_id)
    fname = message.from_user.first_name
    uid = message.from_user.id
    if user:
        fname = name
        uid = user

    if groupType not in ["group", "supergroup"]:
        bot.send_message(
            chat_id, "You have to add me to a group first and type /newgame there!"
        )
        return  # Exit the function here

    if not game:
        bot.send_message(
            chat_id, "There is no game in this chat. Create a new game with /newgame"
        )
        return

    if game.game_phase != "waiting_for_players":
        bot.send_message(
            chat_id, "The game has started. Please wait for the next game!"
        )
        return

    if uid in game.players:
        bot.send_message(chat_id, "You already joined the game, %s!" % fname)
        return

    if len(game.players) >= 10:
        bot.send_message(
            chat_id,
            "You have reached the maximum amount of players. Please start the game with /startgame!",
        )
        return

    try:
        bot.send_message(
            uid,
            f"You joined a game in {group_name}. I will soon tell you your secret role.",
        )
        # If all conditions are passed, add the player
        game.add_player(uid, fname)
    except Exception:
        bot.send_message(
            chat_id,
            fname
            + ", I can't send you a private message. Please go to Bot's chat and click 'Start'.\nYou then need to send /join again.",
        )

    else:
        if len(game.players) > 4:
            bot.send_message(
                chat_id,
                fname
                + " has joined the game. Type /startgame if this was the last player and you want to start with %d players!"
                % len(game.players),
            )
        else:
            bot.send_message(
                chat_id,
                "%s has joined the game. There are currently %d players in the game and you need 5-10 players."
                % (fname, len(game.players)),
            )


@bot.message_handler(commands=["cancelgame"])
def cancel_game(message):
    chat_id = message.chat.id
    game = GamesController.get_game(chat_id)
    # or is_admin(message.from_user.id, chat_id)
    if game:
        if message.from_user.id == game.initiator_id:
            GamesController.end_game(chat_id)
            bot.reply_to(message, "The game has been cancelled.")
        else:
            bot.reply_to(
                message,
                "Only the initiator of the game or a group admin can cancel the game with /cancelgame",
            )
    else:
        bot.reply_to(
            message, "There is no game in this chat. Create a new game with /newgame"
        )


@bot.message_handler(commands=["board"])
def show_board(message):
    chat_id = message.chat.id
    game = GamesController.get_game(chat_id)
    if game:
        board = game.get_board().print_board()
        bot.send_message(chat_id, board)
    else:
        bot.send_message(chat_id, "No game in progress.")


@bot.message_handler(commands=["help"])
def send_help(message):
    chat_id = message.chat.id
    help_text = "Here are the available commands:\n" + "\n".join(commands)
    bot.send_message(chat_id, help_text)


@bot.message_handler(commands=["ping"])
def send_ping(message):
    bot.send_message(message.chag.id, "Pong (v420.69)")


@bot.message_handler(commands=["symbols"])
def send_symbols(message):
    chat_id = message.chat.id
    symbols_text = "Here are the game symbols:\n" + "\n".join(symbols)
    bot.send_message(chat_id, symbols_text)


@bot.message_handler(commands=["calltovote"])
def calltovote(message):
    try:
        chat_id = message.chat.id
        if chat_id in GamesController.games.keys():
            game = GamesController.games.get(chat_id, None)
            if not game.dateinitvote:
                bot.send_message(chat_id, "The voting didn't start yet.")
            else:
                start = game.dateinitvote
                stop = datetime.datetime.now()
                elapsed = stop - start
                if elapsed > datetime.timedelta(minutes=0):
                    history_text = ""
                    for player in game.player_sequence:
                        if player.user_id not in game.votes:
                            history_text += f"It's time to vote [{game.get_player_name_by_id(player.user_id)}](tg://user?id={player.user_id}).\n"
                    bot.send_message(chat_id, text=history_text, parse_mode="Markdown")
                else:
                    bot.send_message(
                        chat_id, "Five minutes must pass to see call to vote"
                    )
        else:
            bot.send_message(
                chat_id,
                "There is no game in this chat. Create a new game with /newgame",
            )
    except Exception as e:
        bot.send_message(chat_id, str(e))


bot.infinity_polling()
