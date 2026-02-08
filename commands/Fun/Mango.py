from botutils import *
import sqlite3


class Mango(Command):
    description = ""
    authorizationLevel = AuthorizationLevel.MEMBER
    syntax = [[], [Lexeme.ACTION], [Lexeme.TEXT], [Lexeme.TEXT, Lexeme.USER], [Lexeme.ACTION, Lexeme.USER, Lexeme.INT]]

    async def run(self, context, args):
        action, pinged = (args + [None] * 2)[:2]

        CLAIM = ["!", "claim", "get", "nom", "add", "take", "mine", "minenow"]
        GIVE = [">", "give", "gib", "given", "fren", "foru", "forchu"]
        LET = ["/", "let", "rm", "remove", "place", "public", "nuhuh", "nuh", "no"]
        SEE = ["v", "see", "watch", "list", "ls", "howmany", "howmuch", "owo"]
        LEADERBOARD = ["?", "leaderboard", "ldb", "top", "who", "whobest" "ewe"]

        msg = "Something went wrong! Ohnoeees! Sorry I couldn't exhaust your wishes! :c"

        def updateMangoCount(user, count, add=True):
            with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
                cur = con.cursor()
                # Command that gives a value 'birthday' equal to amount of days before their bday comes. If bday is past, adds 1 to year (with the CASE section). Used to order them in "coming order"
                res = cur.execute(f"SELECT mango FROM mango WHERE user = ?", (user,))
                res = res.fetchone()

                if res is None:
                    if count > 0:
                        cur.execute("""
                                    INSERT INTO mango (user, mango)
                                    VALUES (?, ?)
                                    """, (user, count))
                        con.commit()
                        mango = count
                    else:
                        return -1
                else:
                    if add: mango = res[0] + count
                    else:   mango = count
                    if mango >= 0:
                        cur.execute("""
                                    UPDATE mango
                                    SET mango = ?
                                    WHERE user = ?
                                    """, (mango, user))
                    else:
                        mango = mango - count
                        return -1

            return mango

        def claim():
            mangos = self.bot.readJSONFrom(MANGO_FILE)

            if not mangos['mangos']:
                return -2

            userID = str(context.author.id)

            if userID in mangos['users']:
                if mangos['users'][userID]['count'] == self.bot.settings['mango']['userLimit']['value']:
                    return -1

            mangos['mangos'] = mangos['mangos'][1:]  # Removes one mango from the list.

            if userID in mangos['users']:
                mangos['users'][userID]['count'] += 1
            else:
                mangos['users'][userID] = {}
                mangos['users'][userID]['count'] = 1

            val = updateMangoCount(context.author.id, +1)

            self.bot.writeJSONTo(MANGO_FILE, mangos)

            return val

        def give():
            if not pinged:
                return -1

            if updateMangoCount(context.author.id, -1) >= 0:
                if updateMangoCount(pinged.id, 1):
                    return 0
                return -3
            return -2

        def let():
            mangos = self.bot.readJSONFrom(MANGO_FILE)

            if len(mangos['mangos']) == self.bot.settings['mango']['limit']['value']:
                return -1

            if updateMangoCount(context.author.id, -1) >= 0:
                mangos['mangos'].append({"delay": 0})
                self.bot.writeJSONTo(MANGO_FILE, mangos)
                return 0
            return -2

        def see():
            with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
                cur = con.cursor()
                # Command that gives a value 'birthday' equal to amount of days before their bday comes. If bday is past, adds 1 to year (with the CASE section). Used to order them in "coming order"
                res = cur.execute(f"SELECT mango FROM mango WHERE user = {context.author.id}")
                res = res.fetchone()

            usMangos = 0
            if res is not None: usMangos = res[0]

            mangoes = self.bot.readJSONFrom(MANGO_FILE)

            return usMangos, len(mangoes['mangos'])

        def leaderboard():
            with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
                cur = con.cursor()
                # Command that gives a value 'birthday' equal to amount of days before their bday comes. If bday is past, adds 1 to year (with the CASE section). Used to order them in "coming order"
                res = cur.execute(f"SELECT * FROM mango ORDER BY mango DESC LIMIT 5")
                res = res.fetchall()

                if res is None:
                    return f"❌ There is no one in the leaderboard! Grab some mangoes to claim the first spot!"

                msg = ""
                if len(res) >= 1: msg += f"🥇 **<@{res[0][0]}>** with **{res[0][1]}** mangoes. 🥭\n"
                if len(res) >= 2: msg += f"🥈 **<@{res[1][0]}>** with **{res[1][1]}** mangoes. 🥭\n"
                if len(res) >= 3:
                    msg += f"🥉 **<@{res[2][0]}>** with **{res[2][1]}** mangoes. 🥭\n"
                    res = res[3:]
                    place = 4
                    for i in res:
                        msg += f"{place}th: **<@{i[0]}>** with {i[1]} mangoes. 🥭\n"
                        place += 1

                return msg

        if action in CLAIM:
            val = claim()
            if val == -2:
                msg = f"Looks like there's no more mango in stock! :c"
            elif val == -1:
                msg = f"🔨 Hey <@{context.author.id}>, share some mangoes with the others! >:C You'll be able to grab some more when the next batch arrives."
            elif val >= 0:
                msg = f"I just added 1 mango 🥭 to your account, <@{context.author.id}>! You now have {val} mango(s)!"

        elif action in GIVE:
            val = give()
            if val == -3:
                msg = f"❌ Something went wrong, but it shouldn't have... A mod will look into this!"
            elif val == -2:
                msg = f"⚫ You don't have any mango to give!"
            elif val == -1:
                msg = f"Please @ the user you want to give the mango to!"
            else:
                msg = f"<@{context.author.id}>, I just gave 1 mango to <@{pinged.id}>"

        elif action in LET:
            val = let()
            if val == -2:
                msg = f"⚫ You don't have any mango to release in public!"
            elif val == -1:
                msg = f"❌ There is already the maximum amount of mangoes in public! You can't add anymore!"
            else:
                msg = f"⬅️🥭 You just deposited a mango in the public, accessible by everyone!"

        elif action in SEE:
            userMangoes, totalMangoes = see()
            msg = f"You have **{userMangoes}** mangoes!\n\nCurrently, there are {totalMangoes} mangoes sitting in public!\n"
            for i in range(0, totalMangoes): msg += "🥭"

        elif action in LEADERBOARD:
            msg = leaderboard()
            embed = self.bot.getDefaultEmbed("🥭 Mango leaderboard 🥭", msg, context.author)
            await context.channel.send(embed=embed)
            return

        elif action in COMMAND_HELP:
            msg = (
                f"Welcome to the mango game! <: Every single day, mangoes will be added to the public area, notified by a message! 🥭\n"
                f"You can grab {self.bot.settings['mango']['userLimit']['value']} mango(es) per day!\n\n"

                f"To start things off, you can **claim public mangoes** with `!mango claim`.\n"
                f"You can **give mangoes to others** if you're feeling generous by typing `!mango give @user`!\n"
                f"You can **release a mango in the public** area for everyone else to grab with `!mango let`.\n"
                f"You can **check your mango balance** (and how many there are in public) with `!mango see`!\n"
                f"And finally, you can **check the leaderboard** with `!mango leaderboard`!\n\n"

                f"Have fun grabbing those mangoes!")

        elif action in COMMAND_UPDATE:
            if AuthorizationLevel.getMemberAuthorizationLevel(context.author.id) >= AuthorizationLevel.PRIVILEGED:
                if len(args) == 3:  count = args[2]
                else:               count = 0
                val = updateMangoCount(pinged.id, count, False)

                msg = f"User <@{pinged.id}> now has {val} mango(es)!"

        else:
            userMangoes, totalMangoes = see()
            msg = f"You have **{userMangoes}** mangoes!\n\nCurrently, there are {totalMangoes} mangoes sitting in public:\n"
            for i in range(0, totalMangoes): msg += "🥭"
            for i in range(totalMangoes, self.bot.settings['mango']['limit']['value']): msg += "⚫"

        await context.channel.send(msg)