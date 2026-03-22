from botutils import *
import discord
from random import randint

class Gamble(Command):
    description = ("Gamble your mango at the grrrreat and powerrful Mango casino! 🥭\n"
                   "You can just type `!gamble` to gamble one mango on black. Otherwise you can type `!gamble <amount> (bet)`: "
                   "for more details: 'bet' can be equal to 'red', 'black', or even a number between 1 and 36!"
                   "If you get the correct color, you will gain the amount you bet, and if you get the correct number, "
                   "you will gain **36** times your bet (big wowies)\n")
    authorizationLevel = AuthorizationLevel.MEMBER
    syntax = [[], [Lexeme.INT], [Lexeme.INT, Lexeme.INT], [Lexeme.INT, Lexeme.TEXT]]
    aliases = ["gambles", "gamble", "letsgogambling"]

    async def run(self, context, args):
        amount, betsOn = (args + [None] * 2)[:2]

        if amount is None or amount <= 0: amount = 1
        if betsOn is None: betsOn = "black"

        # Checks if user has enough mangoes:
        mangoBalance = self.bot.getMangoBalance(context.author.id)

        if mangoBalance < amount:
            await context.channel.send(f"You cheeky pone, you don't have enough mango to do that! You have {mangoBalance} in your account!")
            return

        number = randint(0, 36) # Rolls a number
        color = "green" if number == 0 else None
        if color is None:
            color = "red" if number % 2 == 0 else "black"

        if color == "green":
            msg = f"🟢{number} | "
        else:
            msg = f"⚫{number} | " if number % 2 == 1 else f"🔴{number} | "


        if isinstance(betsOn, int) and 0 <= betsOn <= 36:
            if number != betsOn:
                amount = -amount
            else: amount = amount * 35

        elif betsOn != color:
            amount = -amount


        else:
            await context.channel.send(f"❌ Sorry, I didn't understand that. Your bet should be 'red', 'black', or a number between 0 and 36.")
            return

        mangoes = self.bot.updateMangoCount(context.author.id, amount)


        if amount == 0: msg = "You just gambled 0 mangoes! D:"
        elif amount > 0: msg += f"🥭 Yippee, you won! You just got {amount} mangoes added! You now have {mangoes} mangoes."
        else: msg += f"Oh noo, you've lost {-amount} mangoes :c You still have {mangoes} mangoes though!"

        await context.channel.send(msg)