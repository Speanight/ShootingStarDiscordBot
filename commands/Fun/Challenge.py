from botutils import *
from Objects.GameSession import *
from random import randint

JOIN_DELAY = 5 # seconds

class Challenge(Command):
    description = ("Do you want to compete against other members and bet some mangoes on some games? "
                   "Well, you now can by using the !challenge command! Just type !challenge <game> <bet>"
                   f" to open a lobby. People will then have {JOIN_DELAY} seconds to jump-in, in this "
                   "winner takes all mini-game!\n"
                   "You can also just type !challenge to see the different games!")
    authorizationLevel = AuthorizationLevel.MEMBER
    syntax = [[], [Lexeme.INT], [Lexeme.TEXT], [Lexeme.INT, Lexeme.INT], [Lexeme.TEXT, Lexeme.INT]]
    aliases = ["game", "gaming", "games", "challonge", "challenges", "versus", "vs"]

    async def run(self, context, args):
        games = self.bot.readJSONFrom(GAMES_FILE)
        game, bet = (args + [None] * 2)[:2]

        # If user wants a list of available games:
        if game is None and bet is None:
            msg = self.description + "\n\nHere is a list of the available games:"

            for i, j in self.bot.gameHandler.games.items():
                msg += "\n" + f"- **{j.name} (id: {i.value})**: `{j.rules}` (between {j.minPlayers} and {j.maxPlayers} players)"

            await context.channel.send(embed=self.bot.getDefaultEmbed("List of games", msg, context.author))
            return

        # Check if the game is recognized:
        game = self.bot.gameHandler.getGame(game)
        if game is None:
            await context.channel.send(f"❗ I do not recognize that game, sorry!")
            return


        if bet is None or bet == 0: bet = self.bot.gameHandler.defaultBet

        message = await context.channel.send(f"**{context.author.name}** is starting a **{game.name}** challenge with a bet of **{bet}**!")
        thread = await message.create_thread(name=f"{game.name} challenge! [Bet: {bet} 🥭]")

        # Add new entry in games:
        session = GameSession(self.bot, game, [context.author.id], bet, thread.id)
        games[str(thread.id)] = session.toJson()
        self.bot.writeJSONTo(GAMES_FILE, games)
        self.bot.gameHandler.addSession(session)
        await message.add_reaction('✅')

        # Waits for people to ready up.
        await asyncio.sleep(JOIN_DELAY)

        games = self.bot.readJSONFrom(GAMES_FILE) # Refreshes json to get latest infos
        currSess = games[str(thread.id)]
        session = GameSession(self.bot, game, currSess["users"], currSess["bet"], thread.id)
        # Check if game has already been started (amount of people met)
        if session.started: return

        # Else, we start manually at end of timer.
        session.started = True
        games[str(thread.id)]["started"] = True

        # If game doesn't start because of lack of players, we delete it.
        if not await game.start(session):
            del games[str(thread.id)]
            await self.bot.gameHandler.removeSession(session)

        self.bot.writeJSONTo(GAMES_FILE, games)