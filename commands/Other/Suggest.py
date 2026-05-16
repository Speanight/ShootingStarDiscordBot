from botutils import *

# Suggestion values (for database)
SUGGEST_AWAIT = 0
SUGGEST_ACCEPTED = 1
SUGGEST_DENIED = 2
SUGGEST_LATER = 3
SUGGEST_REPOST = 4

class Suggest(Command):
    description = ("Do you have a suggestion to make the server or my content better? You can use this command to send your requests"
                   "in a channel, where people will be able to vote if they want to see your changes included or not!\n"
                   "Admins can mark suggestions as accepted, denied, 'to-do later' or as a report with !suggest <id> <yes/no/maybe/repost/copy>")
    authorizationLevel = AuthorizationLevel.MEMBER
    syntax = [[Lexeme.TEXT], [Lexeme.INT, Lexeme.TEXT]]
    aliases = ["suggestion", "sugg", "sug", "suggests", "want", "wanties"]

    def addToDb(self, msg, user):
        with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO suggestion (user, message) VALUES (?, ?)",
                        (user.id, msg.id))
            id = cur.lastrowid

        return id

    def modifyDb(self, id, user, status):
        with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
            cur = con.cursor()
            cur.execute("UPDATE suggestion SET status = ?, mod = ? WHERE id = ?",
                        (status, user.id, id))
            cur.execute("SELECT message FROM suggestion WHERE id = ?", (id,))
            msgId = cur.fetchone()

        return msgId[0]

    async def run(self, context, args):
        channel = self.bot.settings["defaultValues"]["channel"]["suggestion"]["value"]

        if channel is None:
            await context.channel.send(f"❌ Sorry, but no suggestion channel has been set! Ask a mod if the command is disabled, or yell at the owner to fix the issue!")
            return

        channel = self.bot.get_channel(channel)

        # If a user tries to add a new suggestion:
        if len(args) == 1:
            suggestion = args[0]

            embed = self.bot.getDefaultEmbed("Suggestion [NOT YET ADDED]", suggestion, context.author, 0x000000)

            msg = await channel.send(embed=embed)
            id = self.addToDb(msg, context.author)

            embed.title = f"Suggestion #{id} - PENDING..."
            embed.colour = 0xebc106

            await msg.edit(embed=embed)
            await msg.add_reaction('👍')
            await msg.add_reaction('👎')
            await msg.create_thread(name=f"Suggestion discussion")

        # Else, a mod is trying to edit a suggestion status:
        else:
            if AuthorizationLevel.getMemberAuthorizationLevel(context.author).value >= AuthorizationLevel.STAFF.value:
                suggestion, status = args[0], args[1]

                # Check status wanted by admin:
                if status in ["yes", "accept", "accepted", "accepts", "confirm"]:
                    st = SUGGEST_ACCEPTED
                elif status in ["no", "deny", "denied", "reject", "rejected", "denies"]:
                    st = SUGGEST_DENIED
                elif status in ["later", "eventually", "maybe", "todo", "soon"]:
                    st = SUGGEST_LATER
                elif status in ["repost", "re", "rep", "copy", "copycat", "ctrl+c"]:
                    st = SUGGEST_REPOST
                else:
                    st = SUGGEST_AWAIT

                msgId = self.modifyDb(suggestion, context.author, st)

                message = await channel.fetch_message(msgId)
                embed = message.embeds[0]
                embed.title = f"Suggestion #{suggestion} - "
                if st == SUGGEST_AWAIT:
                    embed.title += "PENDING..."
                    embed.colour = 0xebc106
                elif st == SUGGEST_DENIED:
                    embed.title += "DENIED"
                    embed.colour = 0xff0000
                elif st == SUGGEST_LATER:
                    embed.title += "Thinking about it"
                    embed.colour = 0xb9a394
                elif st == SUGGEST_REPOST:
                    embed.title += "REPOST"
                    embed.colour = 0xdad4ef
                elif st == SUGGEST_ACCEPTED:
                    embed.title += "ACCEPTED"
                    embed.colour = 0x8cff98

                await message.edit(embed=embed)
                await context.channel.send(f"✅ I have successfully modified the status of the suggestion #{suggestion}!")

            else:
                await context.channel.send(f"You can't do that! You do not have the permissions for this.")
