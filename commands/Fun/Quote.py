from botutils import *
from random import randrange

"""
Quote command. Adds/get a random quote from a json file. JSON file can be shared to a website or something
for use with Streamer.Bot.

@return JSONs objects are structured like this:
{int ID=0, int lastInsertedId, int amtQuotes} <- 1st elem. '0' used to know it's safe to modify.
{int ID, int timestamp, int authorID, string author, string text, int owner}
"""
class Quote(Command):
    description = ('Allows you to add, list or get details of a quote.\n'
                   'You can get one random quote by typing !quote.\n'
                   'To add a quote, use !quote add "quote" (@user) (@timestamp). Both user and timestamp are not necessary.\n'
                   'To list quotes, use !quote list\n'
                   'To get details of a quote, use !quote <QuoteID>.\n'
                   'You can also modify a quote by typing !quote update @user @timestamp.\n'
                   'Finally, you can remove a quote if you\'re its owner, author, or a mod. Simply type quote rm <quoteID>.')
    authorizationLevel = AuthorizationLevel.MEMBER
    syntax = [[], [Lexeme.INT], [Lexeme.ACTION], [Lexeme.ACTION, Lexeme.TEXT],
              [Lexeme.ACTION, Lexeme.TEXT, Lexeme.USER],
              [Lexeme.ACTION, Lexeme.TEXT, Lexeme.USER, Lexeme.DATETIME],
              [Lexeme.ACTION, Lexeme.INT],
              [Lexeme.ACTION, Lexeme.INT, Lexeme.USER],
              [Lexeme.ACTION, Lexeme.INT, Lexeme.USER, Lexeme.DATETIME]]
    aliases = ["quotes", "q"]

    async def run(self, context, args):
        quotes = self.bot.readJSONFrom('jsons/quotes.json')
        if quotes == {}: quotes = [{"id": 0, "lastInsertedId": 0, "amtQuotes": 0}]

        action, info, user, timestamp = (args + [None] * 4)[:4]

        def getQuoteById(quoteID):
            for i in quotes:
                if i["id"] == quoteID:
                    return i
            return None

        # !quote
        if action is None:
            # Get a random quote
            if (len(quotes) == 1):
                await context.channel.send(f"👉 You need to add a quote first!")
                return
            rnd = randrange(1, len(quotes))

            quote = quotes[rnd]
            msg = f'> "{quote["text"]}"'
            if quote["author"] is not None: u = self.bot.get_user(quote["author"])
            else: u = context.author

            embed = self.bot.getDefaultEmbed(f"📑 Quote #{quote['id']}", msg, u)

            await context.channel.send(embed=embed)
            return

        # !quote <ID>
        elif isinstance(action, int):
            # Get a quote by its ID
            quote = getQuoteById(action)
            if quote is None: return
            if quote["author"] is not None: u = discord.utils.get(self.bot.guild.members, name=quote["author"])
            else: u = context.author

            msg = f'> "{quote["text"]}"'

            if quote["timestamp"] is not None: msg += f"\n\n <t:{quote['timestamp']}:F> (<t:{quote['timestamp']}:R>)"

            embed = self.bot.getDefaultEmbed(f"📑 Quote #{quote['id']}", msg, u)

            await context.channel.send(embed=embed)
            return

        # !quote <ACTION>
        else:
            # !quote + (text)
            if action in COMMAND_ADD:
                # We want to add a quote
                quote = {"text": info, "owner": context.author.id, "author": None, "timestamp": None}

                if user is not None:
                    quote["author"] = user.name

                if timestamp is not None:
                    quote["timestamp"] = round(timestamp.timestamp())

                if quotes[0]["id"] == 0:
                    quote["id"] = quotes[0]["lastInsertedId"] + 1
                    quotes[0]["lastInsertedId"] += 1
                    quotes[0]["amtQuotes"] += 1

                else:
                    await context.channel.send(f"❌ Oops, I couldn't add the quote! D:")
                    return

                quotes.append(quote)

                # Adds the quote to the JSON file
                self.bot.writeJSONTo('jsons/quotes.json', quotes)
                await context.channel.send(f"✅ Quote #{quote['id']} added!")
                return

            # !quote =
            elif action in COMMAND_LIST:
                msg = ""

                for i in quotes[1:]:
                    msg += f"- `{i['id']}`: {i['text'][:25]}"
                    if len(i['text']) > 25: msg += "..."
                    msg += "\n"

                embed = self.bot.getDefaultEmbed(f"📑 List of quotes", msg, context.author)
                await context.channel.send(embed=embed)
                return

            # !quote # <ID> @user >timestamp
            elif action in COMMAND_UPDATE:
                # Modify a quote:
                quote = getQuoteById(info)
                if quote['author'] == context.author.id or quote['owner'] == context.author.id or AuthorizationLevel.getMemberAuthorizationLevel(context.author).value >= AuthorizationLevel.STAFF:
                    if user is not None:
                        quote["author"] = user.name
                    if timestamp is not None:
                        quote["timestamp"] = timestamp

                    quotes.remove(quote)
                    quotes.append(quote)

                    await context.channel.send(f"✅ Quote #{quote['id']} successfully updated!")
                    return

                await context.channel.send(f"❌ I couldn't update the quote! Only the quote owner, author, or a mod can do that!")
                return


            # !quote - <ID>
            elif action in COMMAND_RM:
                # Removes a quote
                quote = getQuoteById(info)

                if quote['author'] == context.author.id or quote['owner'] == context.author.id or AuthorizationLevel.getMemberAuthorizationLevel(context.author).value >= AuthorizationLevel.STAFF:
                    quotes.remove(quote)
                    quotes[0]["amtQuotes"] -= 1
                    self.bot.writeJSONTo('jsons/quotes.json', quotes)

                    await context.channel.send(f"✅ Quote #{quote['id']} removed!")
                    return

                await context.channel.send(f"❌ I couldn't remove the quote! Only the quote owner, author, or a mod can do that!")
                return