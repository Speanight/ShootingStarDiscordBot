from botutils import *
import discord
import sqlite3
import datetime
from datetime import timedelta, timezone

class Privilege(Command):
    description = ("Allows to get/add users with privilege for a limited period of time.\n"
                   "__privilege get (all)__ allows you to get current (or all) privileged users.\n"
                   "__privilege add <USER> (minutes [int])__ allows you to give privileges to user for x minutes. Defaults to 5.")
    authorizationLevel = AuthorizationLevel.OWNER
    syntax = [[Lexeme.ACTION, Lexeme.USER], [Lexeme.ACTION, Lexeme.USER, Lexeme.INT], [Lexeme.ACTION, Lexeme.TEXT],
              [Lexeme.ACTION]]

    async def run(self, context, args):
        action = args[0]

        def addPrivileges(user, time):
            if user == self.bot.user:
                return False
            if user.id == self.bot.settings['moderation']['owner']['value']:
                return False

            now = datetime.now(timezone.utc)
            until = now + timedelta(minutes=time)

            with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
                cur = con.cursor()
                cur.execute("""
                            INSERT INTO privilege (user, endsAt)
                            VALUES (?, ?)
                            """, (user.id, until))
                con.commit()

            return True

        def getPrivileges(getall):
            privileged = getPrivileged(None, getall)

            description = '\n'.join(
                f"- <@{p['user']}>: from <t:{p['startsAt']}:f> to <t:{p['endsAt']}:f> (<t:{p['endsAt']}:R>)".strip()
                for p in privileged)
            if not privileged: description = "__No match for the current search!__"

            return description

        # Adds new privileged user:
        if action in COMMAND_ADD and (isinstance(args[1], discord.User) or isinstance(args[1], discord.Member)):
            user = args[1]
            time = 5
            if len(args) == 3: time = args[2]
            if addPrivileges(user, time):
                await context.channel.send(f"✅ I successfully privileged <@{user.id}> for {time} minutes!")
            else:
                await context.channel.send(
                    f"❌ I couldn't privilege <@{user}>, sorry... Was user the owner, or the bot itself?")

        # Gets privileged users:
        elif action in COMMAND_PREVIEW:
            getall = len(args) == 2 and args[1] == "all"
            desc = getPrivileges(getall)

            title = "Privileged list"
            if getall: title += " - All"

            embed = self.bot.getDefaultEmbed(title, desc, context.author)

            await context.channel.send(embed=embed)

        else:
            await context.channel.send(f"❓ I did not understand what you meant by the action {action}, sorry!")