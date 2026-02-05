from botutils import Command, AuthorizationLevel, Lexeme, DB_FOLDER, COMMAND_LIST
import sqlite3

class Say(Command):
    description = (
        "Makes me say TEXT in CHANNEL (if specified, otherwise I'll talk in the same one as the one this command has been sent in!)\n"
        "It is also possible to check messages that has been sent with the LIST action. A message ID can also be given as an argument.")
    authorizationLevel = AuthorizationLevel.STAFF
    syntax = [[Lexeme.TEXT], [Lexeme.CHANNEL, Lexeme.TEXT], [Lexeme.ACTION], [Lexeme.ACTION, Lexeme.INT]]

    async def run(self, context, args):
        # TODO: check that say command is working.
        if args[0] == COMMAND_LIST:
            msgId = None
            query = "SELECT * FROM message"
            if len(args) == 2:
                msgId = args[1]
                query += f" WHERE message = {msgId}"

            with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
                cur = con.cursor()
                res = cur.execute(query)
                res = res.fetchall()

            if not res:
                if msgId is not None:
                    msg = f"❌ No message found!"
                else:
                    msg = f"📃 No message has been sent with the bot yet! Try it out with `!say TEXT`!"
            else:
                if msgId is not None:
                    msg = f"The message https://discord.com/channels/{self.bot.guild.id}/{res[0]['channel']}/{res[0]['message']} has been sent by <@{res[0]['user']}"
                else:
                    msg = ""
                    for i in res:
                        msg += f"- https://discord.com/channels/{self.bot.guild.id}/{res[0]['channel']}/{res[0]['message']} has been sent by <@{res[0]['user']} | sent by <@{i['user']}>"

            await self.bot.getDefaultEmbed("Say checkout", msg, context.author)


        else:
            channel = context.channel
            if len(args) == 2: channel = args[0]
            message = args[-1]
            await self.bot.sendMessage(channel, message, context.author)