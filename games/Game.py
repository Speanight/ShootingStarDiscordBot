from enum import Enum
from Objects.GameSession import GameSession
import asyncio


class GameType(Enum):
    TYPERACER = 1


class Game:
    def __init__(self, name = "", id = -1, minPlayers = 2, maxPlayers = 2):
        self.name = name
        self.id = id
        self.minPlayers = minPlayers
        self.maxPlayers = maxPlayers
        self.rules = ""

    async def start(self, session : GameSession):
        if self.minPlayers <= len(session.users) <= self.maxPlayers:
            msg = f"⏰ The game's going to start! **{len(session.users)} players** have been registered:\n"
            for i in session.users:
                msg += f"<@{i.id}> ; "
            msg = msg[:-2] + "- Get ready!"
            await session.thread.send(msg)
            return True # Signals to keep game as it is playing right now.
        else:
            await session.thread.send(f"I am sorry, but the amount of players doesn't match with the"
                                      f" requirements for this game! :c \nTry again later perhaps!")
            return False # Signals to delete game because it didn't start

    async def handleWinner(self, session : GameSession, winner):
        if winner not in session.users: return False

        for i in session.users:
            if i == winner: session.bot.updateMangoCount(i, session.bet, True)
            else: session.bot.updateMangoCount(i, -session.bet, True)

        await session.thread.send(f"<@{winner.id}> wins! The thread will close shortly...")

        await asyncio.sleep(5)

        msg = await session.thread.fetch_message(session.thread.id)
        await msg.edit(f"🏆 <@{winner.id}> won the {session.game.name} game and won {session.bet} mangoes!")

        return True