# player.py
import random
import discord
from discord.ext import commands
from typing import Dict, List


class Player:
    def __init__(self, user: discord.User) -> None:
        self.dice = [str(random.choice(range(1, 7))) for _ in range(6)]
        self.user = user
        self.knights = []
        self.score = 0
        self.reroll = False
        self.dice_in_play = []
        self.dice_indexes = []

    @property
    def name(self) -> str:
        return self.user.name

    def print_dice(self) -> str:
        if len(self.dice) == 0:
            return "No dice left\n"
        else:
            return self.user.name + "'s dice rolls are: ||" + " ".join(map(str,self.dice)) + "||\n"


    def swap(self, die = "none") -> List[str]:
        if die == "none":
            return "No dice used"
        else:
            self.dice[die-1] = str(random.choice(range(1,7)))
            return self.print_dice()
