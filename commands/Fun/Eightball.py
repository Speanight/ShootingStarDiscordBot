from botutils import *
import random
from datetime import datetime

class Eightball(Command):
    name = "8ball"
    description = "8ball command: asks it anything, and it shall give you THE answer (definitely not something random trust)"
    authorizationLevel = AuthorizationLevel.MEMBER
    aliases = ["eightball", "ball"]

    async def run(self, context, args):
        answers = ["Definitely!", "Yes!", "Most likely.", "As I see it, yes", "Signs point to yes.", "Yes.",
                   "Ask again later", "Better keep that secret...", "I'm not sure",
                   "Nuh-uh!", "No", "Nope!", "Very doubtful", "No way!", "Impossible."]
        random.seed(datetime.now().timestamp())
        await context.channel.send(random.choice(answers))