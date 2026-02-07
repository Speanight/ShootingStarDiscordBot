from botutils import *
import discord

class Status(Command):
    description = \
        ("Modifies my custom status! No argument (or empty string) to delete it. Gets overwritten by twitch status setting!\n"
        "If status is equal to refresh and twitch status is activated, refreshes the status of the bot.")
    authorizationLevel = AuthorizationLevel.STAFF
    syntax = [[], [Lexeme.TEXT]]

    async def run(self, context, args):
        if not args:
            message = ""
        elif args[0] == "refresh":
            self.twitchStatus()
        else:
            if not self.bot.settings['twitch']['schedule']['automaticStatus']['value']:
                if self.bot.updateSetting(['twitch', 'schedule', 'automaticStatus'], True):
                    await context.channel.send(
                        f"✅ Removed automatic status for the twitch channel to display new status!")
                else:
                    await context.channel.send(
                        f"❌ Couldn't remove automatic status for the twitch channel. Displayed status might get erased soon. Try setting it to False manually with settings command.")
            message = args[0]
        await self.bot.change_presence(activity=discord.Game(name=message))