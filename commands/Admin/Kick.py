from botutils import *
import discord

class Kick(Command):
    description = "Kicks USER from server, with given reason - if specified."
    authorizationLevel = AuthorizationLevel.STAFF
    syntax = [[Lexeme.USER], [Lexeme.USER, Lexeme.TEXT]]

    async def run(self, context, args):
        user = args[0]
        if len(args) == 1:
            reason = ""
        else:
            reason = args[1]

        try:
            await user.kick(reason=reason)
            if self.bot.addModAction(context.author, user, ModActions.KICK.value, reason):
                await context.channel.send(f"{args[0].display_name} has been successfully kicked!")
                logChannel = self.bot.settings['logs']['channel']['value']
                if logChannel is None: return
                embed = self.bot.getDefaultEmbed("User kick",
                                                 f"{user.name} has been kicked by {context.author.name}, with reason {reason}",
                                                 context.author, 0xff0000)
                await logChannel.send(embed=embed)

            else:
                await context.channel.send(f"You are not allowed to take action on this user!")
        except discord.errors.Forbidden:
            await context.channel.send(f'`Kick error: impossible to kick user {user.name}`')