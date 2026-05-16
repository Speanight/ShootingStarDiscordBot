from botutils import *

ACHIEVEMENTS_FILE = "jsons/achievements"

class Achievement(Command):
    description = ("You can accomplish various achievements in this server, or through twitch or whatever! "
                   "You can take a look at your achievements with this command.\n"
                   "Some of the achievements are hidden in plain sight... And some of them are secrets! It's up to you "
                   "to discover how to unlock them (or you could ask for some tips, hints, or eventually someone else!")
    authorizationLevel = AuthorizationLevel.MEMBER
    syntax = [[], [Lexeme.ACTION, Lexeme.TEXT]]
    aliases = ["achievements", "success", "achieve", "trophy", "trophies"]
    lockdown = True # To remove when command is completed

    # TODO: continue achievements

    async def run(self, context, args):
        achievements = self.bot.readJSONFrom(ACHIEVEMENTS_FILE)

