from botutils import *

class Quote(Command):
    description = ('Allows you to add, list or get details of a quote.\n'
                   'To add a quote, use !quote add <@user> "quote".\n'
                   'To list quotes, just use !quote\n'
                   'To get details of a quote, use !quote get <QuoteID>.')
    authorizationLevel = AuthorizationLevel.MEMBER
    syntax = [[], [Lexeme.ACTION, Lexeme.USER, Lexeme.TEXT], [Lexeme.ACTION, Lexeme.INT]]

    lockdown = True

    async def run(self, context, args):
        pass