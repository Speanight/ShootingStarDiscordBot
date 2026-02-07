from botutils import *
from datetime import datetime

class Uptime(Command):
    description = "Shows how long Shooting Star has been online for."
    authorizationLevel = AuthorizationLevel.TRIALSTAFF
    syntax = [[]]

    async def run(self, context, args):
        startTime = self.bot.startTime.strftime('%d/%m/%Y %H:%M')
        uptime = datetime.now() - self.bot.startTime
        await context.channel.send(f"I'm awake since {startTime}.\nMy current uptime is {uptime.days} day(s).")