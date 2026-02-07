from botutils import *
import sqlite3
from datetime import datetime, timedelta

class Birthday(Command):
    description = (
        "Shooting Star can wish you happy birthday! Add your birthday with __!birthday add DD/MM__ (or DD/MM/YYYY if you want her to know your age too!)\n"
        "If you want to show the next X birthdays, you just have to type __!birthday X__ (or without argument to show the next few ones)!\n"
        "She can also forget your birthday with __!birthday remove__")
    authorizationLevel = AuthorizationLevel.MEMBER
    syntax = [[], [Lexeme.INT], [Lexeme.ACTION, Lexeme.DATE], [Lexeme.ACTION]]
    aliases = ['bday', 'bd', 'birth']

    async def run(self, context, args):
        msg, embed = None, None

        def getNextBirthdays(limit):
            def getNextOccurence(rawDate):
                now = datetime.now()
                bdayDay = datetime.strptime(rawDate[0:10], '%Y-%m-%d').replace(year=now.year)

                if now > bdayDay: bdayDay = bdayDay.replace(year=now.year + 1)

                return bdayDay + timedelta(hours=14)

            if limit > 20: limit = 20
            # Display the next X birthday
            with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
                cur = con.cursor()
                # Command that gives a value 'birthday' equal to amount of days before their bday comes. If bday is past, adds 1 to year (with the CASE section). Used to order them in "coming order"
                res = cur.execute(
                    f"SELECT user, day, julianday(CASE WHEN date(strftime('%Y', 'now') || '-' || strftime('%m-%d', day)) < date('now') THEN strftime('%Y', 'now', '+1 year') || '-' || strftime('%m-%d', day) ELSE strftime('%Y', 'now') || '-' || strftime('%m-%d', day) END) - julianday(date('now')) AS birthday FROM birthday ORDER BY birthday LIMIT {limit}")
                res = res.fetchall()

                if not res:
                    return self.bot.getDefaultEmbed("Incoming birthdays",
                                                    f"❓ I don't know the birthday of anyone here! You can add yours by typing birthday add DD/MM!",
                                                    context.author)

                msg = ""
                for i in res:
                    date = getNextOccurence(i[1])

                    entry = {"user": f"<@{i[0]}>", "bday": date}
                    if entry['bday'].month == datetime.now().month and entry['bday'].day == datetime.now().day:
                        msg += f"> {entry['user']} | 🎂 TODAY! WISH THEM HAPPY BDAY!\n\n"
                    else:
                        msg += f"> {entry['user']} | <t:{int(entry['bday'].timestamp())}:d> (<t:{int(entry['bday'].timestamp())}:R>)\n"
                return self.bot.getDefaultEmbed("Incoming birthdays", msg, context.author)

        def addBirthday(date, user=context.author.id):
            # Adds new birthday
            with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
                cur = con.cursor()
                res = cur.execute(f"SELECT * FROM birthday WHERE user = {user}")
                res = res.fetchall()  # id, day

                if res:
                    return f"⚠️ I already knew your birthday, silly!"
                if date:
                    cur.execute("""
                                INSERT INTO birthday (user, day)
                                VALUES (?, ?)
                                """, (user, date))
                    con.commit()
                    return "✅ I successfully saved your birthday in my database!"
                else:
                    return "❓ I didn't understand the date you gave me, sorry... Make sure it's in format DD/MM or DD/MM/YYYY"

        def removeBirthday(user=context.author.id):
            # Deletes the birthday
            with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
                cur = con.cursor()
                cur.execute(f"DELETE FROM birthday WHERE user = {user}")
                con.commit()
                return f"✅ I deleted your birthday from my memory!"

        if len(args) == 0 or isinstance(args[0], int):
            if len(args) == 0:
                limit = 10
            else:
                limit = args[0]
            embed = getNextBirthdays(limit)
            await context.channel.send(embed=embed)
            return

        elif args[0] in COMMAND_ADD:
            msg = addBirthday(args[1], context.author.id)
        elif args[0] in COMMAND_RM:
            msg = removeBirthday()
        else:
            # None of that: unknown request
            await context.channel.send(f"❌ I didn't understand what you meant by '{args[0]}', sorry!")
        if msg is not None:
            await context.channel.send(msg)
        elif embed is not None:
            await context.channel.send(embed=embed)