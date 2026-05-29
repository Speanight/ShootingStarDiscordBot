from Objects.GameSession import *
from botutils import *
from games import TypeRacer
from games.TicTacToe import TicTacToe
from games.TypeRacer import *
import asyncio


class GameHandler:
    def __init__(self, bot):
        self.bot = bot
        # Init. all existing games:
        self.games = {
            GameType.TYPERACER.value: TypeRacer(),
            GameType.TICTACTOE.value: TicTacToe()
        }
        self.defaultBet = 10

        # Init. all ongoing game sessions:
        self.gameSessions = {}

    def getGame(self, game):
        if game in self.games:
            return self.games[game]

        if game in ["typeracer", "type", "race", "typeracing", "10fastfingers"]:
            return self.games[GameType.TYPERACER]

        return None


    def addSession(self, session):
        self.gameSessions[session.thread.id] = session

    async def removeSession(self, session):
        del self.gameSessions[session.thread.id]
        await session.thread.edit(locked=True, archived=True)


    async def messageHandler(self, message):
        if message.channel.id not in self.gameSessions: return None # Not in a game channel

        game = self.gameSessions[message.channel.id]
        # Check that user participates in the game:
        if message.author in game.users:
            if await game.game.handleMessage(game, message):
                # A user won: close session.
                await self.removeSession(game)
        else: return False # From user not participating

        return True # Handled correctly.


    async def reactionHandler(self, reaction, user):
        # Check if reaction is for a game session:
        if reaction.message.id not in self.gameSessions: return None
        game = self.gameSessions[reaction.message.id]

        # Check if reaction is to ready up:
        if reaction.emoji == "✅" and not game.started:
            # Check that user isn't already registered:
            if user in game.users:
                await game.thread.send(f"<@{user.id}>, you are already participating!")
                return
            # Check if game can still accept people:
            if len(game.users) <= game.game.maxPlayers:
                if self.bot.getMangoBalance(user.id) >= game.bet:
                    game.users.append(user)
                    await game.thread.send(f"✅ <@{user.id}>, I have successfully added you to the session!")
                else:
                    await game.thread.send(f"🥭 You don't have enough mangoes to participate, <@{user.id}>! The bet is currently at {game.bet}.")
            else:
                await game.thread.send(f"❌ I'm sorry <@{user.id}>, but the game already has the maximum amount of people in it!")

            if game.users == game.game.maxPlayers:
                await game.thread.send(f"🔒 This game session reached the maximum amount of people! The game will start shortly...")
                await asyncio.sleep(1)
                await game.game.start(game)

            return True
        return False
