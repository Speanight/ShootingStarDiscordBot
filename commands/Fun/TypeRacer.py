from botutils import *
from Objects.Game import *
from random import randint

class TypeRacer(Command):
    description = ("Typeracer is a game where you can bet some mangoes as to who types the fastest! The "
                   "bot will take a random text and will send it. The users will then need to copy and "
                   "send the text as quickly as possible: the first one will receive all the mangoes!")
    authorizationLevel = AuthorizationLevel.MEMBER
    syntax = [[Lexeme.USER, Lexeme.INT], [Lexeme.USER], [Lexeme.INT, Lexeme.USER]]
    aliases = ["typerace", "type", "keyboardrace", "keyboardracer", "keyboardracers"]

    async def run(self, context, args):
        games = self.bot.readJSONFrom(GAMES_FILE)

        user, bet = (args + [None] * 2)[:2]
        if type(user) == int: bet, user = user, bet
        if bet is None or bet == 0: bet = games["settings"]["typeracer"]["defaultBet"]

        if user == context.author:
            await context.channel.send(f"You can't challenge yourself silly!")
            return

        message = await context.channel.send(f"**{context.author.name}** is challenging **{user.name}** "
                                             f"to a type-racer! The bet is **{bet}** mangoes, and the "
                                             f"winner will get {2*bet}! Waiting for both users to "
                                             f"react with ✅ before starting!")

        textId = randint(0, len(games["settings"]["typeracer"]["texts"]))
        val = {"textId": textId,
               "text": {games["settings"]["typeracer"]["texts"][textId]}}

        game = Game(GameType.TYPERACER, message.id, [context.author.id, user.id], bet)
        game.values = val


