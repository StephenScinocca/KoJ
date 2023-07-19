# import random

# list1 = [sum(random.choice(range(1,7))  for i in range(0,3)) for i in range(1,100001)]
# list2 = [sum(random.choice(range(1,7))  for i in range(0,4)) for i in range(1,100001)]
# list3 = [1 for i in range(1,len(list1)) if list1[i] > list2[i] ]
# list4 = [1 for i in range(1,len(list1)) if list1[i] == list2[i] ]

# ties = len(list4)
# total = sum(list3)/(100000.0 - ties)

# l = [1,2,3,4,6]

# l = [7-i for i in l]

# print(l)

# This example requires the 'message_content' intent.

import discord
import os
import logging
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')


intents = discord.Intents.default()
intents.message_content = True
# intents.messages = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        print(message.author)
        return

    if message.content.startswith('koj'):
        await message.channel.send('Hello!')
    # else:
    #     await print(message.content)

client.run(TOKEN, log_handler=handler)