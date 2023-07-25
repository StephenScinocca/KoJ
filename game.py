# game.py
import os
import random
import discord
from dotenv import load_dotenv
from discord.ext import commands
from enum import Enum
from typing import Dict, List

from player import Player

knights = ["Crystal", "Blood", "Storm", "Leaf", "Sun", "Moon", "Shadow", "Flower", "Earth"]

class GameState (Enum):

    # no game started
    NO_GAME = 0
    # One player in
    WAITING = 1
    # roll 6 d6
    ROLLED  = 2
    # Pick Heroes
    PICKING = 3
    # Rounds
    ROUNDS = 4
    # END Game
    END = 5


class Game:
    def __init__(self, message) -> None:
       self.new_game(message)


    def new_game(self, message: discord.Message):
        self.state = GameState.NO_GAME
        self.players: List[Player] = []
        self.total_rerolls = False
        self.knights  =  ["Crystal", "Blood", "Storm", "Leaf", "Sun", "Moon", "Shadow", "Flower", "Earth"]
        self.turn  = 0
        self.round_score = [0, 0]
        self.game_score = [0, 0]
        self.round_number = 1
        self.p1_played = False
        self.p2_played = False
        self.crystal = 0
        self.channel = message.channel

    def add_player(self, user:discord.User) -> bool:
        if self.is_player(user) != None:
            return False
        self.players.append(Player(user))
        return True

    # Returns whether a user is playing in the game
    def is_player(self, user: discord.User) -> Player:
        for player in self.players:
            if player.user == user:
                return player
        return None

    async def swap_dice(self, user :discord.User, die) -> List[str]:
        for player in self.players:
            if player.user == user:
                return player.swap(die)
        else:
            return "User is not in this game"

    async def rolls(self, user :discord.User) -> List[str]:
        for player in self.players:
            if player.user == user:
                return player.print_dice()
        else:
            return "User is not in this game"

    def pick_knight(self, user: discord.User, picked_knight) -> str:
        if self.turn == 0 or self.turn == 3 or self.turn == 4:
            player = self.players[0]
        else:
            player = self.players[1]
        if player.user == user:
                self.knights.remove(picked_knight)
                player.knights.append(picked_knight)
                self.turn = self.turn + 1
                if self.turn == 6:
                    self.state = GameState.ROUNDS
                return "Added knight\n"
        else:
            return "Not this players turn"

    def dice_used(self, user: discord.User, dice_used) -> str:
        cur_player = self.is_player(user)
        cur_player.dice_indexes = dice_used
        if cur_player != None:
            # Checks Dice not used
            for index in dice_used:
                if index > 6 or index < 1:
                    return "Dice index out of bounds"
                die = cur_player.dice[index - 1]
                if die == "NULL":
                    return "Cannot add a dice used already"
            # Checks Flower Knight
            if self.players[0].knights[(self.round_number-1)] == "Flower" or self.players[1].knights[(self.round_number-1)] == "Flower":
                for index in dice_used:
                    if '5' in cur_player.dice[(int(index)-1)] or '6' in cur_player.dice[(int(index)-1)]:
                        return "Cannot use any dice bigger than 4 this round"
            # Checks Earth Knight
            for player in self.players:
                if player != cur_player and player.knights[(self.round_number-1)] == "Earth" and len(dice_used) > 2:
                    return "Cannot use more than 2 dice this round"
            for index in dice_used:
                die = cur_player.dice[index - 1]
                cur_player.dice_in_play.append(die)
                cur_player.dice[index - 1] = "NULL"
            if cur_player == self.players[0]:
                self.p1_played = True
            if cur_player == self.players[1]:
                self.p2_played = True
            if len(cur_player.dice_in_play) == 0:
                    return "None"
            return str(cur_player.dice_in_play) + "\n"
        else:
            return "User is not in this game"


    def reset_round(self):
        self.round_score[0] = 0
        self.round_score[1] = 0
        self.players[0].dice_in_play = []
        self.players[1].dice_in_play = []
        self.p1_played = False
        self.p2_played = False


    def calculate(self) -> int:
        score = 0
        temp = ""
        for index in range(0,len(self.players)):
            for die in self.players[index].dice_in_play:
                score =  score + int(die)
            self.round_score[index] = self.round_score[index] + score
            score = 0
        temp = temp + self.players[0].name + "\'s score is " + str(self.round_score[0]) + "\n"
        temp = temp + self.players[1].name + "\'s score is " + str(self.round_score[1]) + "\n"
        if self.round_score[0] > self.round_score[1]:
            temp = temp + self.players[0].name + " wins round " + str(self.round_number) + "\n"
            self.game_score[0] += 1
        elif self.round_score[0] < self.round_score[1]:
            self.game_score[1] += 1
            temp = temp + self.players[1].name + " wins round " + str(self.round_number) + "\n"
        else:
            temp = temp + "WE HAVE A DRAW \n"
            self.game_score[0] += 1
            self.game_score[1] += 1
        self.round_number = self.round_number + 1
        self.reset_round()
        temp = temp + "Game score is: " + str(self.game_score[0]) + " " + str(self.game_score[1]) + "\n"
        if self.game_score[0] == 2 and self.game_score[0] != self.game_score[1]:
            self.state = GameState.END
            temp = temp + self.players[0].name + " wins the game!\n"
        elif self.game_score[1] == 2 and self.game_score[0] != self.game_score[1]:
            self.state = GameState.END
            temp = temp + self.players[1].name + " wins the game!\n"
        elif self.round_number > 3:
            if self.game_score[0] == self.game_score[1]:
                temp = temp + "Game is a draw"
            elif self.game_score[0] > self.game_score[1]:
                temp = temp + self.players[0].name + " wins the game!\n"
            else:
                temp = temp + self.players[1].name + " wins the game!\n"
            self.state = GameState.END
        else:
            temp = temp + "Now we are on round " + str(self.round_number) + "\n"
        return temp

    def use_knights(self):
        cur_round = self.round_number - 1
        p1_knight = self.players[0].knights[cur_round]
        p2_knight = self.players[1].knights[cur_round]
        p1_dice = self.players[0].dice_in_play
        p2_dice = self.players[1].dice_in_play
        temp = ""
        if p1_knight == "Crystal":
            while self.crystal in self.players[1].dice_in_play:
                self.players[1].dice_in_play.remove(self.crystal)
        if p2_knight == "Crystal":
            while self.crystal in self.players[0].dice_in_play:
                self.players[0].dice_in_play.remove(self.crystal)
        if p1_knight == "Storm" or p2_knight == "Storm":
            temp = temp + (self.players[0].name + "\'s old rolls were " + str(self.players[0].dice_in_play)) + "\n"
            self.players[0].dice_in_play = [str(random.choice(range(1, 7))) for _ in range(len(p1_dice))]
            temp = temp + (self.players[0].name + "\'s new rolls are " + str(self.players[0].dice_in_play)) + "\n"
            temp = temp + (self.players[1].name + "\'s old rolls were " + str(self.players[1].dice_in_play)) + "\n"
            self.players[1].dice_in_play = [str(random.choice(range(1, 7))) for _ in range(len(p2_dice))]
            temp = temp + (self.players[1].name + "\'s new rolls are " + str(self.players[1].dice_in_play)) + "\n"
        if p1_knight == "Moon" or p2_knight == "Moon":
            temp = temp + (self.players[0].name + "\'s old rolls were " + str(self.players[0].dice_in_play)) + "\n"
            self.players[0].dice_in_play = [str(7 - int(i)) for i in self.players[0].dice_in_play]
            temp = temp + (self.players[0].name + "\'s new rolls are " + str(self.players[0].dice_in_play)) + "\n"
            temp = temp + (self.players[1].name + "\'s old rolls were " + str(self.players[1].dice_in_play)) + "\n"
            self.players[1].dice_in_play = [str(7 - int(i)) for i in self.players[1].dice_in_play]
            temp = temp + (self.players[1].name + "\'s new rolls are " + str(self.players[1].dice_in_play)) + "\n"
        if p1_knight == "Shadow":
            for i in range(1,7):
                count = self.players[0].dice_in_play.count(str(i))
                # print(count, i)
                while count >= 2:
                    count = count - 2
                    self.round_score[0] = self.round_score[0] + 3
        if p2_knight == "Shadow":
            for i in range(1,7):
                count = self.players[1].dice_in_play.count(str(i))
                # print(count, i)
                while count >= 2:
                    count = count - 2
                    self.round_score[1] = self.round_score[1] + 3
        if p1_knight == "Blood":
            self.round_score[0] = self.round_score[0] + len(p2_dice)
        if p2_knight == "Blood":
            self.round_score[1] = self.round_score[0] + len(p1_dice)
        if p1_knight == "Sun":
            temp = temp + (self.players[0].name + "\'s old rolls were " + str(self.players[0].dice_in_play)) + "\n"
            temp = temp + (self.players[1].name + "\'s old rolls were " + str(self.players[1].dice_in_play)) + "\n"
            max_die = max(self.players[1].dice_in_play)
            min_die = min(self.players[0].dice_in_play)
            self.players[1].dice_in_play.remove(max_die)
            self.players[1].dice_in_play.append(min_die)
            self.players[0].dice_in_play.remove(min_die)
            self.players[0].dice_in_play.append(max_die)
            temp = temp + (self.players[0].name + "\'s new rolls are " + str(self.players[0].dice_in_play)) + "\n"
            temp = temp + (self.players[1].name + "\'s new rolls are " + str(self.players[1].dice_in_play)) + "\n"
        if p2_knight == "Sun":
            temp = temp + (self.players[0].name + "\'s old rolls were " + str(self.players[0].dice_in_play)) + "\n"
            max_die = max(self.players[0].dice_in_play)
            min_die = min(self.players[1].dice_in_play)
            self.players[0].dice_in_play.remove(max_die)
            self.players[0].dice_in_play.append(min_die)
            temp = temp + (self.players[0].name + "\'s new rolls are " + str(self.players[0].dice_in_play)) + "\n"
            temp = temp + (self.players[1].name + "\'s old rolls were " + str(self.players[1].dice_in_play)) + "\n"
            self.players[1].dice_in_play.remove(min_die)
            self.players[1].dice_in_play.append(max_die)
            temp = temp + (self.players[1].name + "\'s new rolls are " + str(self.players[1].dice_in_play)) + "\n"
        if p1_knight == "Leaf":
            print(self.players[0].dice_in_play)
            for i in range(len(self.players[0].dice_in_play)):
                print(self.players[0].dice_in_play[i])
                if self.players[0].dice_in_play[i] == '1':
                    print(self.players[0].dice[(self.players[0].dice_indexes[i] - 1)])
                    self.players[0].dice[(self.players[0].dice_indexes[i] - 1)] = 1
                if self.players[0].dice_in_play[i] == '2':
                    print(self.players[0].dice[(self.players[0].dice_indexes[i] - 1)])
                    self.players[0].dice[(self.players[0].dice_indexes[i] - 1)] = 2
        if p2_knight == "Leaf":
            print(self.players[1].dice_in_play)
            for i in range(len(self.players[1].dice_in_play)):
                print(self.players[1].dice_in_play[i])
                if self.players[1].dice_in_play[i] == '1':
                    print(self.players[1].dice[(self.players[1].dice_indexes[i] - 1)])
                    self.players[1].dice[(self.players[1].dice_indexes[i] - 1)] = 1
                if self.players[1].dice_in_play[i] == '2':
                    print(self.players[1].dice[(self.players[1].dice_indexes[i] - 1)])
                    self.players[1].dice[(self.players[1].dice_indexes[i] - 1)] = 2

        return temp
