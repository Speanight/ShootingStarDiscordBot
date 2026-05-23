from enum import Enum
import json

class GameType(Enum):
    TYPERACER = 1

class Game:
    def __init__(self, game=None, channel=None, users=None, bet=None, values=None):
        self.game = game
        self.channel = channel
        self.users = users
        self.bet = bet
        self.values = values

    def toJson(self):
        return json.dumps(self.__dict__)