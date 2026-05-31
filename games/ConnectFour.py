import discord
from games.Game import *


ROWS = 6
COLUMNS = 7


SIGNS = ["⬛", "🔴", "🟡"]

class ConnectFour(Game):
    def __init__(self):
        super().__init__("ConnectFour", GameType.CONNECTFOUR.value, 2, 2)
        self.rules = ("Connect-4 is a game where players take turn placing pieces in a board. The objective is to "
                      "align 4 pieces of the same color horizontally, vertically or diagonally.")


    def drawBoard(self, board):
        msg = ""
        for r in range(ROWS):
            for c in range(COLUMNS):
                msg += SIGNS[board[c][ROWS-r-1]+1]
            msg += "\n"
        msg += ":one::two::three::four::five::six::seven:\n"

        return msg

    def getEmbed(self, session):
        msg = (f"{self.drawBoard(session.values['board'])}\n\n"
               f"To play, just write the number of the column you want to drop your piece in!\n\n"
               f"{SIGNS[1]}: {session.users[0].display_name} / {SIGNS[2]}: {session.users[1].display_name}\n\n"
               f"It is {session.users[session.values["playerTurn"]].display_name}'s turn!")

        embed = discord.Embed(title=self.name, description=msg, color=0xa547c1)
        embed.set_footer(text=f"{session.users[0].display_name} vs {session.users[1].display_name} | Bet: {session.bet}")
        return embed


    def checkWin(self, board, playerTurn):
        # Horizontal check
        for c in range(COLUMNS-3):
            for r in range(ROWS):
                if board[c][r] == board[c+1][r] == board[c+2][r] == board[c+3][r] == playerTurn:
                    return True

        # Vertical check
        for c in range(COLUMNS):
            for r in range(ROWS-3):
                if board[c][r] == board[c][r+1] == board[c][r+2] == board[c][r+3] == playerTurn:
                    return True

        # Diagonal checks
        for c in range(COLUMNS-3):
            for r in range(ROWS-3):
                if board[c][r] == board[c+1][r+1] == board[c+2][r+2] == board[c+3][r+3] == playerTurn:
                    return True

        for c in range(3, COLUMNS):
            for r in range(ROWS-3):
                if board[c][r] == board[c-1][r+1] == board[c-2][r+2] == board[c-3][r+3] == playerTurn:
                    return True

        return False

    def getCorrectRow(self, board, column):
        for r in range(ROWS):
            if board[column][r] == -1:
                return r
        return None

    async def start(self, session):
        result = await super().start(session)
        if not result: return result

        # Game:
        session.values["board"] = [[-1 for _ in range(ROWS)] for _ in range(COLUMNS)]
        session.values["playerTurn"] = 0

        await session.thread.send(embed=self.getEmbed(session))

        return True

    async def handleMessage(self, session, message: discord.Message):
        # Should return true in case of a winner, false if nothing and none if player not in game/command invalid
        input = int(message.content)
        if input in list(range(COLUMNS+1)):
            input -= 1
            if message.author == session.users[session.values["playerTurn"]]:
                # Places the piece at the top of the board:
                row = self.getCorrectRow(session.values["board"], input)
                if row is None:
                    await session.thread.send(f"You didn't select a correct row!")
                    return None

                session.values["board"][input][row] = session.values["playerTurn"]
                session.values["playerTurn"] = (session.values["playerTurn"] + 1)%2

                await session.thread.send(embed=self.getEmbed(session))

                if self.checkWin(session.values["board"], (session.values["playerTurn"] + 1)%2):
                    await self.handleWinner(session, message.author)
                    return True

                # Check for draw:
                if all(cell != -1 for c in session.values["board"] for cell in c):
                    await self.handleWinner(session, None)
                    return True


                return False
            else: return None
        else: return None