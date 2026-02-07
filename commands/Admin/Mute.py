from botutils import *
from datetime import datetime, timedelta

class Mute(Command):
    description = ("Mutes a user for specified time and reason\n"
                   "Quick reminder that a 'duration' should be used with this syntax: 1d2h3m to mute the user"
                   "for one day, two hours and three minutes.")
    authorizationLevel = AuthorizationLevel.TRIALSTAFF
    syntax = [[Lexeme.USER], [Lexeme.USER, Lexeme.DURATION], [Lexeme.USER, Lexeme.TEXT, Lexeme.DURATION],
              [Lexeme.USER, Lexeme.DURATION, Lexeme.TEXT]]

    async def run(self, context, args):
        if self.bot.settings['moderation']['muted']['value'] is None:
            await context.channel.send(
                "❗ No muted role has been attributed. Therefor, mutes are unavailable. Please ask owner or privileged to set it with settings command.")
            return
        user, reason = args[0], ""
        time = {"days": 0, "hours": 0, "minutes": self.bot.settings['defaultValues']['muteTime']['value']}
        if len(args) >= 2:
            if type(args[1]) is dict:
                time = args[1]
            else:
                reason = args[1]

            if len(args) == 3:
                if type(args[2]) is dict:
                    time = args[2]
                else:
                    reason = args[2]

        id = self.bot.addModAction(context.author, user, ModActions.MUTE.value,
                                   reason + f" | {time['days']}d{time['hours']}h{time['minutes']}m")
        if id is not False:
            modactions = self.bot.readJSONFrom('jsons/modactions.json')
            pardon = datetime.now() + timedelta(days=time['days'], hours=time['hours'], minutes=time['minutes'])
            if modactions == {}: modactions = []
            modactions.append(
                {"id": id, "user": user.id, "pardon": pardon.timestamp(), "action": ModActions.MUTE.value})
            self.bot.writeJSONTo('jsons/modactions.json', modactions)

            if len(modactions) == 1:
                print(f"Starting modActionsPardon!")
                await self.bot.modActionPardon()

            await user.add_roles(get(self.bot.guild.roles, id=self.bot.settings['moderation']['muted']['value']))
            await context.channel.send(
                f"{user.display_name} has been muted for {time['days']}d{time['hours']}h{time['minutes']}m!")