from botutils import *

class Shop(Command):
    description = ("You've worked hard enough to get some mangoes? Or perhaps you gambled them away and was lucky enough "
                   "to gamble them away and get more than what you initially had, and now you want to spend them?\n"
                   "Well, the shop is here exactly for this reason!")
    authorizationLevel = AuthorizationLevel.MEMBER
    syntax = [[], [Lexeme.ACTION, Lexeme.ROLE], [Lexeme.INT]]

    async def run(self, context, args):
        # User wants to display shop:
        if len(args) == 0:
            pass

        # User wants to buy something from the shop:
        elif len(args) == 1:
            pass

        # Mod wants to add something in the shop:
        elif len(args) == 2 and AuthorizationLevel.getMemberAuthorizationLevel(context.author).value >= AuthorizationLevel.STAFF.value:
            pass