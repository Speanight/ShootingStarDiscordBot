from botutils import *

class PlanMessage(Command):
    description = ('Allows the bot to plan sending a message at a specific time. Here are the expected syntaxes:\n'
                   '__planMessage add <CHANNEL> <DATETIME> "<TEXT>"__ to add a new planned text.\n'
                   '__planMessage remove <ID>__ to remove a planned text.\n'
                   '__planMessage list__ to list all the planned messages.\n'
                   '__planMessage <ID>__ to preview the message in the context channel.')
    authorizationLevel = AuthorizationLevel.STAFF
    syntax = [[Lexeme.ACTION, Lexeme.CHANNEL, Lexeme.DATETIME, Lexeme.TEXT], [Lexeme.ACTION, Lexeme.INT], [Lexeme.ACTION], [Lexeme.INT]]

    async def run(self, context, args):
        action = args[0]
        async def addMessage(channel, day, content):
            plannedMsg = self.bot.readJSONFrom('jsons/plannedMessages.json')
            if plannedMsg == {}: plannedMsg = []

            # Checks if message has an embed...
            attach = []
            for i in context.message.attachments:
                attach.append(i.filename)
                await i.save(f'files/{i.filename}')


            msg = {'id': len(plannedMsg ) +1, 'channel': channel.id, 'time': int(day.timestamp()), 'msg': content, 'embed': attach, 'author': context.author.id}
            plannedMsg.append(msg)
            self.bot.writeJSONTo('jsons/plannedMessages.json', plannedMsg)
            if len(plannedMsg) == 1:
                print(f"Starting message planner!")
                self.bot.messagePlanner.start()
            return len(plannedMsg)

        def removeMessage(id):
            plannedMsg = self.bot.readJSONFrom('jsons/plannedMessages.json')
            for i in plannedMsg:
                if i['id'] == id:
                    plannedMsg.remove(i)
                    self.bot.writeJSONTo('jsons/plannedMessages.json', plannedMsg)
                    if len(plannedMsg) == 0:
                        print(f"Stopping message planner!")
                        self.bot.messagePlanner.stop()
                    return True
            return False

        def listMessages():
            plannedMsg = self.bot.readJSONFrom('jsons/plannedMessages.json')
            if not plannedMsg: msg = f"No planned message!"
            else: msg = ""
            for i in plannedMsg:
                msg += f"- **ID:** {i['id']} - <t:{i['time']}:F> | {i['msg'][:25]}...\n"
            return msg

        def getMessage(id):
            plannedMsg = self.bot.readJSONFrom('jsons/plannedMessages.json')
            for i in plannedMsg:
                if i['id'] == id:
                    return i
            return None

        emb = False
        # If trying to add a new message:
        if action in COMMAND_ADD:
            idPlanned = await addMessage(args[1], args[2], args[3])
            msg = f"✅ Your message *(ID: {idPlanned})* has successfully been added to the list!"
        elif action in ["remove", "rm", "-"]:
            if removeMessage(args[1]):
                msg = "🗑️ Your message has successfully been removed!"
            else:
                msg = "❗ Your message couldn't be found!"
        # If trying to list all planned messages:
        elif action in COMMAND_LIST:
            msg = listMessages()
            emb = True
        # If trying to preview a specific message:
        elif action in COMMAND_PREVIEW:
            pmsg = getMessage(args[1])
            if pmsg is not None:
                msg = f"{pmsg['msg']}"
            else:
                msg = "❗ Sorry, your message could not be found!"
        else:
            msg = "❓ I did not understand the action you wanted. Please use one of those: `add`, `remove`, `list`, `preview`"

        if emb:
            embed = self.bot.getDefaultEmbed("Message", msg, context.author)
            await context.channel.send(embed=embed)
        else:
            await context.channel.send(msg)