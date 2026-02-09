from botutils import *
import discord
from random import randint

class Gamble(Command):
    description = ("Gamble your mango at the grrrreat and powerrful Mango casino! 🥭\n"
                   "You can just type `!gamble` to gamble one mango on red. Otherwise you can type `!gamble <amount> <bet>` "
                   "for more details: 'bet' can be equal to 'red', 'black', or even a number between 1 and 36!"
                   "If you get the correct color, you will gain the amount you bet, and if you get the correct number, "
                   "you will gain **36** times your bet (big wowies)")
    authorizationLevel = AuthorizationLevel.MEMBER
    syntax = [[], [Lexeme.INT], [Lexeme.INT, Lexeme.TEXT], [Lexeme.INT, Lexeme.INT]]
    aliases = ["gambles", "gamble", "letsgogambling"]

    async def run(self, context, args):
        amount, betsOn = (args + [None] * 2)[:2]

        if not amount: amount = 1

        colors = randint(1, 2) # 1 = red / 2 = black
        number = randint(1, 18)
        if colors == 1:
            number = number * 2 - 1
            msg = f"⚫{number} | "
        else:
            number = number * 2
            msg = f"🔴{number} | "

        if ((betsOn is None or betsOn == "red") and colors == 1) or (betsOn == "black" and colors == 2):
            amount = -amount

        elif isinstance(betsOn, int):
            if 1 <= betsOn <= 36:
                if number != betsOn:
                    amount = - amount
                else: amount = amount * 36

        mangoes = self.bot.updateMangoCount(context.author.id, amount)


        if amount > 0: msg += f"🥭 Yippee, you won! You just got {amount} mangoes added! You now have {mangoes} mangoes."
        else: msg += f"Oh noo, you've lost {-amount} mangoes :c You still have {mangoes} mangoes though!"

        await context.channel.send(msg)