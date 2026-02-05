from botutils import Command, AuthorizationLevel, Lexeme, ModActions
import discord
from datetime import datetime, timedelta

class Ban(Command):
    description = ("Bans USER from server with given reason - if specified - and deletes the messages sent by them"
                   "in the last X (max. 7) days.\n"
                   "You may also temporarily ban a user by typing a duration."
                   "(ie: 1d2h3m bans for 1 days, 2 hours and 3 minutes)\n"
                   "__Except 'user', none of the arguments are required.__ Correct syntaxes are following:"
                   "ban <user> <reason> <duration> <deleteTime>\n")
    authorizationLevel = AuthorizationLevel.ADMIN
    syntax = [[Lexeme.USER], [Lexeme.USER, Lexeme.TEXT], [Lexeme.USER, Lexeme.TEXT, Lexeme.DURATION],
              [Lexeme.USER, Lexeme.TEXT, Lexeme.DURATION, Lexeme.INT]]

    async def run(self, context, args):
        user, reason, duration, deleteTime = (args + [None] * 4)[:4]

        if deleteTime is not None:
            reason += f" - messages over the last {deleteTime} days have been deleted"
        else:
            deleteTime = 0
        try:
            r = reason
            if duration is not None:
                r += " - " + duration
            id = self.bot.addModAction(context.author, user, ModActions.BAN.value, r)
            if id is not False:
                await self.bot.guild.ban(user=user, reason=reason, delete_message_days=deleteTime)
                # await user.ban(reason=reason, delete_message_days=deleteTime)
                await context.channel.send(f"✅ {args[0].display_name} has been successfully banned!")
                if duration is not None:
                    modactions = self.bot.readJSONFrom('jsons/modactions.json')
                    pardon = datetime.now() + timedelta(days=duration['days'], hours=duration['hours'],
                                                        minutes=duration['minutes'])
                    if modactions == {}: modactions = []
                    modactions.append(
                        {"id": id, "user": user.id, "pardon": pardon.timestamp(), "action": ModActions.BAN.value})
                    self.bot.writeJSONTo('jsons/modactions.json', modactions)
                    if len(modactions) == 1:
                        self.bot.modActionPardon.start()
            else:
                await context.channel.send(
                    f"❌ The ban couldn't be done. Perhaps the user has higher authorization than you?")
        except discord.errors.Forbidden:
            await context.channel.send(f'❌ `Ban error: impossible to ban user {user.name}`')