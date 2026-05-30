import discord
from pip._internal.network import session
from copy import copy, deepcopy

from games.Game import *

SIGNS = ["⬛", "❌", "⭕"]

class TicTacToe(Game):
    def __init__(self):
        super().__init__("TicTacToe", GameType.TICTACTOE.value, 2, 2)
        self.rules = (f"Classic tic-tac-toe game! Players will take turn placing one of their "
                      f"pieces on a 3x3 grid. The objective is to align 3 of your pieces in a row! "
                      f"If no player achieves to do that and the board is fully filled, a draw happens!")

    def drawBoard(self, board):
        # TODO: do it properly with a loop cause this looks like pain
        msg = (f"```\n"
                f"----------\n"
                f"|{SIGNS[board[0][0]+1]}|{SIGNS[board[0][1]+1]}|{SIGNS[board[0][2]+1]}|\n"
                f"----------\n"
                f"|{SIGNS[board[1][0]+1]}|{SIGNS[board[1][1]+1]}|{SIGNS[board[1][2]+1]}|\n"
                f"----------\n"
                f"|{SIGNS[board[2][0]+1]}|{SIGNS[board[2][1]+1]}|{SIGNS[board[2][2]+1]}|\n"
                f"----------\n"
                f"```")

        return msg

    def checkWin(self, board, playerTurn):
        for i in range(3):
            if board[i][i] == playerTurn and (board[0][i] == board[1][i] == board[2][i] or board[i][0] == board[i][1] == board[i][2]):
                return True

        if board[1][1] == playerTurn and (board[0][0] == board[1][1] == board[2][2] or board[0][2] == board[1][1] == board[2][0]):
            return True
        return False

    def getEmbed(self, session):
        msg = (f"{self.drawBoard(session.values['board'])}\n\n"
               f"To play, just write the number of the tile where you want to play. (1-9, 1 being top left, 9 being bottom right and 4 being middle left)\n\n"
               f"{SIGNS[1]}: {session.users[0].display_name} / {SIGNS[2]}: {session.users[1].display_name}\n\n"
               f"It is {session.users[session.values["playerTurn"]].display_name}s turn!")
        embed = discord.Embed(title="TicTacToe", description=msg, color=0xa547c1)
        embed.set_footer(text=f"{session.users[0].display_name} vs {session.users[1].display_name} | Bet: {session.bet}")
        return embed

    async def start(self, session):
        result = await super().start(session)
        if not result: return result

        # Game:
        session.values["board"] = [[-1, -1, -1], [-1, -1, -1], [-1, -1, -1]]
        session.values["playerTurn"] = 0
        await session.thread.send(embed=self.getEmbed(session))
        return True

    async def handleMessage(self, session, message: discord.Message):
        # Check if value given is a number between 1 and 9:
        input = int(message.content)
        if input in list(range(1,10)):
            input -= 1
            # Check if it's correct player
            if message.author == session.users[session.values["playerTurn"]]:
                # Check if spot is free:
                if session.values["board"][input//3][input%3] == -1:
                    # Updates board:
                    session.values["board"][input//3][input%3] = session.values["playerTurn"]
                    session.values["playerTurn"] = (session.values["playerTurn"] + 1)%2
                    await session.thread.send(embed=self.getEmbed(session))
                    # Needs to do a (+1)%2 cause we change its value just before to display the board.
                    if self.checkWin(session.values["board"], (session.values["playerTurn"]+1)%2):
                        await self.handleWinner(session, message.author)
                        return True

                    if all(cell != -1 for row in session.values["board"] for cell in row):
                        await self.handleWinner(session, None)
                        return True


                    return False
            return None
        else: return None