from botutils import *
from discord.utils import get

class Unmute(Command):
    description = "Unmutes an user if that user was muted before. This will remove any pending duration."
    authorizationLevel = AuthorizationLevel.TRIALSTAFF
    syntax = [[Lexeme.USER]]

    async def run(self, context, args):
        if self.bot.settings['moderation']['muted']['value'] is None:
            await context.channel.send \
                ("❗ No muted role has been attributed. Therefor, mutes are unavailable. Please ask owner or privileged to set it with settings command.")
            return

        user, id = args[0], None

        modactions = self.bot.readJSONFrom('jsons/modactions.json')
        for i in modactions:
            if i['user'] == user.id:
                id = i['id']
                modactions.remove(i)
        if id is not None:
            self.bot.writeJSONTo('jsons/modactions.json', modactions)

        if AuthorizationLevel.getMemberAuthorizationLevel \
                (context.author).value > AuthorizationLevel.getMemberAuthorizationLevel(user).value:
            msg = "✅ The user has been unmuted."
            await user.remove_roles(get(self.bot.guild.roles, id=self.bot.settings['moderation']['muted']['value']))
        else:
            msg = "❌ You are not allowed to unmute this user."

        await context.channel.send(msg)