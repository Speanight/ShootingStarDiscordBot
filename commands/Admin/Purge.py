from botutils import *

class Purge(Command):
    description = "Clears last X messages in the corresponding channel. Defaults to setting value if no number is given."
    authorizationLevel = AuthorizationLevel.TRIALSTAFF
    syntax = [[], [Lexeme.INT]]

    async def run(self, context, args):
        if not args:
            number = self.bot.settings['defaultValues']['purgeAmount']['value']
        else:
            number = args[0]
        await context.channel.purge(limit=number + 1)