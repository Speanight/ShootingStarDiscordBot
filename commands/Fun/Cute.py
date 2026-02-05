from botutils import Command, AuthorizationLevel
import random
from datetime import datetime

class Cute(Command):
    description = "Gives your daily cute % if used without argument."
    authorizationLevel = AuthorizationLevel.MEMBER
    syntax = [[]]

    async def run(self, context, args):
        def getCutePercentage(seed):
            random.seed(seed)
            return random.random() * 100

        # Using cute %age command
        if not args:
            today = datetime.now()
            today = today.replace(hour=0, minute=0, second=0, microsecond=0)
            percent = round(getCutePercentage(context.author.id + today.timestamp()), 2)

            await context.channel.send(f"<@{context.author.id}>, you are **{percent}%** cute today!")