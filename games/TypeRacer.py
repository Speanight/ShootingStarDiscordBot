from games.Game import *

class TypeRacer(Game):
    def __init__(self):
        super().__init__("Typeracer", GameType.TYPERACER.value, 2, 25)
        self.rules = (f"In Typeracer, the bot will send a random sentence, and people will have to type "
                      f"it out as quickly as possible. The one that sends the EXACT sentence (punctuation"
                      f" and caps included!) will win the minigame!")

    async def start(self, session):
        await super().start(session)
        print(f"Start function of game {self.name}")