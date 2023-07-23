# bot.py
import os
import random
import discord
from dotenv import load_dotenv
from discord.ext import commands
from typing import Dict, List
from collections import namedtuple
import logging
from player import Player
from game import Game, GameState
from PIL import Image

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

Eight_Ball = ["Because your parents don't love you", 
            "Because quinn has decreed it as such",
            "LMAO LOSER", 
            "Fate has decreed it so",
            "Nugget", 
            "Why not?", 
            "There is no conceivable way I could comprehend an answer that even basically approaches that question",
            "Sometimes when a man and woman love each other, BOOM ya got preggers", 
            "Who knows man? Probably magic dude",
            "It's a crazy world we live in", 
            "ANYTHINGS POSSIBLE!!!! except the answer to that question", 
            "I would know that if I was alive then",
            "PROCESSSSSSING............................ Nope no clue", 
            "Sure, why not?",
            "NO F***ING WAY AM I GOING TO ANSWER THAT YOU FREAK"]

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')


intents = discord.Intents.default()
intents.message_content = True
# intents.messages = True

client = discord.Client(intents=intents)

# client = discord.Client()

games: Dict[discord.TextChannel, Game] = {}

async def new_game(game: Game, message: discord.Message) -> List[str]:
    if game.state == GameState.NO_GAME:
        game.new_game()
        game.add_player(message.author)
        game.state = GameState.WAITING
        return "A new game has been started by " + message.author.name + "! \nMessage p2 to join the game."
    else:
        messages = ["There is already a game in progress, "
                    "you can't start a new game."]
        if game.state == GameState.WAITING:
            messages.append("It still hasn't started yet, so you can still "
                            "message !start to join that game.")
        return messages

async def join_game(game: Game, message: discord.Message) -> List[str]:
    if game.state == GameState.NO_GAME:
        return ["No game has been started yet for you to join.",
                "Message !newgame to start a new game."]
    elif game.state != GameState.WAITING:
        return [f"The game is already in progress, {message.author.name}.",
                "You're not allowed to join right now."]
    elif game.add_player(message.author):
        concat = await start_game(game, message)
        return message.author.name + " has joined the game!\n\n" + concat
    else:
        return [f"You've already joined the game {message.author.name}!"]

async def rules(game: Game, message: discord.Message):

    # image_paths = ["Images/die_1_OG.png", "Images/die_2_OG.png", "Images/die_3_OG.png"]
    # # Maximum width and height for the resized images
    # max_size = (32, 32)

    # try:
    #     files = []
    #     for path in image_paths:
    #         with Image.open(path) as image:
    #             image.thumbnail(max_size)
    #             image_file = discord.File(image.filename, filename=f"resized_{image.filename}")
    #             files.append(image_file)

    #     await message.channel.send(files=files)
    # except FileNotFoundError:
    #     await message.channel.send("One or more image files not found.")


    try:
        with open("Images/rules.png", "rb") as file:
            image_file = discord.File(file)
            await message.channel.send(file=image_file)
    except FileNotFoundError:
        await message.channel.send("Image file not found.")
    return ""

async def reroll(game: Game, message: discord.Message) -> List[str]:
    if game.state != GameState.ROLLED:
        return 'Cannot reroll now'
    tokens = message.content.split()
    if len(tokens) < 3:
        return "Please add which dice you would like to swap, by adding a number after between 1 - 6 which correspond not with the value of the dice, but the order you see them. "
    if len(tokens) > 3:
        return "Added too many arguments"
    try:
            die = int(tokens[2])
            if die < 0 or die > 6:
                return "Use a dice index between 1 and 6"
            if game.players[0].user == message.author:
                if game.players[0].reroll == True:
                    return "Only 1 reroll is allowed per player"
                elif game.players[1].reroll == True:
                    game.state = GameState.PICKING
                    game.players[0].reroll = True
                    if die != 0:
                        temp = await game.swap_dice(message.author, die)
                        return temp + "\nNow " + game.players[0].name + " picks their first knight"
                    else:
                        return "No dice changed \nNow " + game.players[0].name + " picks their first knight"
                else:
                    game.players[0].reroll = True
                    if die != 0:
                        return await game.swap_dice(message.author, die)
                    else:
                        return "No dice changed"
            elif game.players[1].user == message.author:
                if game.players[1].reroll == True:
                    return "Only 1 reroll is allowed per player"
                elif game.players[0].reroll == True:
                    game.state = GameState.PICKING
                    game.players[1].reroll = True
                    if die != 0:
                        temp = await game.swap_dice(message.author, die)
                        return  temp + "\nNow " + game.players[0].name + " picks their first knight"
                    else:
                        return "No dice changed \nNow " + game.players[0].name + " picks their first knight"
                else:
                    game.players[1].reroll = True
                    if die != 0:
                        return await game.swap_dice(message.author, die)
                    else:
                        return "No dice changed"
            else:
                return "Only 1 reroll is allowed per player"
    except ValueError:
            return "Please follow !reroll with an integer. " + tokens[2] + " is not an integer."

async def rolls(game: Game,  message: discord.Message) -> List[str]:
    return await game.rolls(message.author)


# Internal method, using in join
async def start_game(game: Game, message: discord.Message) -> List[str]:
    concat = ""
    game.state = GameState.ROLLED
    channel = message.channel
    await channel.send("Creating threads")
    threads = []

    
    thread1 = await channel.create_thread(
        name="Player 1",    
        type=discord.ChannelType.private_thread
    )
    thread2 = await channel.create_thread(
        name="Player 2",    
        type=discord.ChannelType.private_thread
    )



    await channel.send("threads created")

    threads.append(thread1)
    threads.append(thread2)
    # await thread1.add_user(message.author)
    # await thread2.add_user(game.players[1])

    for index, player in enumerate(game.players):
        player.thread = threads[index]
        await player.thread.add_user(player.user)
        dice_rolls = player.print_dice()
        concat += dice_rolls
        await player.thread.send(dice_rolls)
    return concat + "Now players may reroll one die by which dice using the command reroll"

# Testing purposes only
async def state(game: Game, message: discord.Message) -> List[str]:
    return game.state

# Gives information on all the knights for each player
def knights(game: Game, message: discord.Message) -> str:
    concat = ''
    for player in game.players:
        concat = concat + player.name + '\'s knights picked: ' + str(player.knights) + '\n'
    concat = concat + "Remaining knights in pool: " + str(game.knights)
    return concat


async def pick(game: Game, message: discord.Message) -> List[str]:
    if game.state != GameState.PICKING:
        return "Cannot pick right now"
    tokens = message.content.split()
    if len(tokens) < 3:
        return "Please add which knight you would like to select, by typing its name. "
    if len(tokens) > 3:
        return "Added too many arguments"
    picked_knight = str(tokens[2]).lower()
    picked_knight = str(picked_knight).capitalize()
    if picked_knight in game.knights:
        concat = game.pick_knight(message.author, picked_knight)
        concat =  concat + "\n" + knights(game, message)
        if game.state == GameState.ROUNDS:
            concat = concat + "\nNow we start round one. Type use and the indexes of the dice you want to play\n"
            for player in game.players:
                concat = concat + player.print_dice()
        return concat
    else:
        return "Invalid knight"

async def use(game: Game, message: discord.Message) -> List[str]:
    # always runs right now for debugging
    if game.state == GameState.ROUNDS:
        tokens = message.content.split()[2:]

        # print(len(tokens))
        tokens = list(map(int, tokens))
        # tokens.sort(reverse = True)
        temp = game.dice_used(message.author, tokens)
        if temp == "Cannot use more than 2 dice this round":
            return temp
        if temp == "Cannot use any dice bigger than 4 this round":
            return temp
        if temp == "Cannot add a dice used already":
            return temp
        if temp == "Dice index out of bounds":
            return temp
        if game.p1_played == True and game.p2_played == True:
            temp = temp + game.use_knights()
            temp = temp + "\n" + game.calculate()
            for player in game.players:
                temp = temp + player.print_dice()
        await game.rolls(game.players[0].user)
        await game.rolls(game.players[1].user)
        return temp
    return "Cannot use right now"

async def end_game(game: Game, message: discord.Message) -> List[str]:
    game.state = GameState.NO_GAME
    game.players: List[Player] = []
    game.total_rerolls = False
    game.knights  =  ["Crystal", "Blood", "Storm", "Leaf", "Sun", "Moon", "Shadow", "Flower", "Earth"]
    game.turn  = 0
    game.p1_round_score = 0
    game.p2_round_score = 0
    game.round_number = 0
    return "Game Reset"

async def die_conversion(number, message):
    emoji_name = "die_{}".format(number)

    custom_emoji = discord.utils.get(message.guild.emojis, name=emoji_name)

    if custom_emoji:
        emoji_id = custom_emoji.id
        # await message.channel.send(f"The ID of the custom emoji {emoji_name} is: {emoji_id}")
    else:
        await message.channel.send(f"Custom emoji {emoji_name} not found.")
        return "" + str(number) + ""

    emoji = "<:{}:{}>".format(emoji_name, emoji_id)

    #     # Send the emoji as a message
    # await message.channel.send(emoji)

    return "" + emoji + " "


async def test(game: Game, message: discord.Message) -> List[str]:


    channel = message.channel
    print("Channel name is ", channel)

    thread = await channel.create_thread(
        name="Player 1",    
        type=discord.ChannelType.private_thread
    )

    await thread.add_user(message.author)

    dice = [str(random.choice(range(1, 7))) for _ in range(6)]

    s = ""
    for die in dice:
        s += await die_conversion(die, message)

    await thread.send(s)

    return s
    # emoji_name = "die_1"

    # # Find the custom emoji by name
    # custom_emoji = discord.utils.get(message.guild.emojis, name=emoji_name)

    # if custom_emoji:
    #     emoji_id = custom_emoji.id
    #     await message.channel.send(f"The ID of the custom emoji {emoji_name} is: {emoji_id}")
    # else:
    #     await message.channel.send(f"Custom emoji {emoji_name} not found.")

    # emoji = "<:{}:{}>".format(emoji_name, emoji_id)

    # #     # Send the emoji as a message
    # await message.channel.send(emoji)
    # # await message.author.send(":die_1: :die_2: :die_3: :die_4: :die_5: :die_6: ") # this message is a DM
    # return ""


async def flip(game: Game, message: discord.Message) -> List[str]:
    value = 0
    value = random.randint(1,2)
    if value == 1:
        return "HEADS"
    elif value == 2:
        return "TAILS"
    else:
        return "QUINN WHY DID YOU MAKE ME DO THIS"

async def show_help(game: Game, message: discord.Message) -> List[str]:
    longest_command = len(max(commands, key=len))
    help_lines = []
    for command, info in sorted(commands.items()):
        spacing = ' ' * (longest_command - len(command) + 2)
        help_lines.append(command + spacing + info[0])
    return "```" + '\n'.join(help_lines) + "```"

# The commands avaliable to the players

Command = namedtuple("Command", ["description", "action"])

commands: Dict[str, Command] = {
    'p1': Command('Starts a new game, and makes person who types it join',
                        new_game),
   'p2':    Command('Lets you join a game that is about to begin',
                       join_game),
    'rules':   Command('Shows the rules of the game',
                        rules),
    'reroll' :   Command('Rerolls one of your dice rolls, by index',
                    reroll),
    'rolls' :   Command('Prints your dice rolls',
                    rolls),
    'start' :   Command('Starts the game',
                    join_game),
    'state' :   Command('For testing purposes, says what state game is in',
                    state),
    'knights' :   Command('Shows all relevant information on the knights',
                    knights),
    'pick' :   Command('For picking knights',
                    pick),
    'use' :   Command('What dice you use for each round',
                    use),
    'reset' :   Command('Resets the game state',
                    end_game),
    'test' :   Command('For testing sending and recieving direct messages',
                    test),
    'help' :   Command('Shows a list of the commands',
                    show_help),
    'flip' :   Command('Shows a list of the commands',
                    flip)

}

@client.event
async def on_ready():
    print("Knights of Justice bot ready!")

@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return
    # Ignore empty messages
    if len(message.content.split()) == 0:
        return
    # Ignore private messages
    #if message.channel.is_private:
    #    return

    tokens = message.content.split()
    if len(tokens) > 1:
        check = tokens[0].lower()
        command = tokens[1].lower()

        if check == 'koj':
            if tokens[-1][-1] == "?":
                await message.channel.send(random.choice(Eight_Ball))
                return
            if command not in commands:
                await message.channel.send(message.content + " is not a valid command. \nMessage !help to see the list of commands.")
                return

            game = games.setdefault(message.channel, Game())
            # try:
            messages = await commands[command][1](game, message)

            # The messages to send to the channel and the messages to send to the
            # players individually must be done seperately, so we check the messages
            # to the channel to see if hands were just dealt, and if so, we tell the
            # players what their hands are.

            # print(message.channel)

            await message.channel.send(messages)
            # if game.state == GameState.END:
            #     messages = end_game(game, message)
            #     await message.channel.send(messages)

# client.run(TOKEN)

client.run(TOKEN, log_handler=handler)
