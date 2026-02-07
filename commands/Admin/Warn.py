from botutils import *

class Warn(Command):
    description = "Warns user for specified reason (if specified)"
    authorizationLevel = AuthorizationLevel.TRIALSTAFF
    syntax = [[Lexeme.USER], [Lexeme.USER, Lexeme.TEXT]]

    async def run(self, context, args):
        if len(args) == 2: reason = args[1]
        else: reason = ""

        if self.bot.addModAction(context.author, args[0], ModActions.WARN.value, reason):
            await context.channel.send(f"{args[0].display_name} has been successfully warned!")
        else:
            await context.channel.send(f"You are not allowed to take action on this user!")