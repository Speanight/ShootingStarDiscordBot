import discord
from botutils import *

class GameSession:
    def __init__(self, bot, game=None, users=None, bet=None, thread=None, started=False):
        if users is None:
            users = []

        self.bot = bot
        self.game = game
        self.users = []
        for i in users:
            self.users.append(self.bot.get_user(i))

        self.thread = self.bot.get_channel(thread)
        self.bet = bet
        self.started = started

        self.values = {} # Will be used by game to keep track of what happened.

    def toJson(self):
        return {
            'game': self.game.id,
            'users': [u.id for u in self.users],
            'bet': self.bet,
            'started': self.started
        }

    async def handleWinner(self, winner : discord.Member):
        for i in self.users:
            if i == winner.id:
                await self.bot.updateMangoCount(winner, self.bet*(len(self.users)-1), True)
            else:
                await self.bot.updateMangoCount(i, -self.bet, True)

        # TODO: finish function
        await self.channel.send()

    async def handleReady(self):
        pass # TODO: Send message if needed, otherwise don't do anything.