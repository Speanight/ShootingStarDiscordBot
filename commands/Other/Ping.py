from botutils import Command, AuthorizationLevel

class Ping(Command):
    description = "Allows you to test connection with me!"
    authorizationLevel = AuthorizationLevel.NONE

    async def run(self, context, args):
        await context.channel.send("pong")