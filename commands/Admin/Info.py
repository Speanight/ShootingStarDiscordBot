from botutils import *
from datetime import datetime, timedelta
import sqlite3

class Info(Command):
    description = "Gets moderating info about USER."
    authorizationLevel = AuthorizationLevel.TRIALSTAFF
    syntax = [[Lexeme.USER]]

    async def run(self, context, args):
        msg = ""
        totActions = {"warn": 0, "mute": 0, "kick": 0, "ban": 0, "lockdown": 0}
        with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
            cur = con.cursor()
            res = cur.execute(f"SELECT * FROM mod_log WHERE user = {args[0].id}")
            res = res.fetchall()  # id, mod, user,action, reason, timestamp, pardon

        if not res: msg = "☀️ Nothing to worry about!"

        for i in res:
            action = {"id": i[0], "mod": i[1], "user": i[2], "action": i[3], "reason": i[4],
                      "timestamp": int(datetime.strptime(i[5], "%Y-%m-%d %H:%M:%S").timestamp()),
                      "pardon": i[6]}
            line = ""
            # Checking action taken...
            if action["action"] == ModActions.WARN.value:
                line = "❗"
                if not action['pardon']: totActions['warn'] += 1
            if action["action"] == ModActions.MUTE.value:
                line = "🔇"
                if not action['pardon']: totActions['mute'] += 1
            if action["action"] == ModActions.KICK.value:
                line = "🥾"
                if not action['pardon']: totActions['kick'] += 1
            if action["action"] == ModActions.BAN.value:
                line = "🔨"
                if not action['pardon']: totActions['ban'] += 1
            if action["action"] == ModActions.LOCKDOWN.value:
                line = "🔒"
                if not action['pardon']: totActions['lockdown'] += 1

            if action['pardon']: line += "~~"
            line += f" _ID: [{action['id']}]_ | <t:{action['timestamp']}:f>, done by <@{action['mod']}>\n"
            if action['reason'] != "": line += f"> **Reason:** {action['reason']}\n"
            if action['pardon']: line += "~~"
            msg += line

        embed = self.bot.getDefaultEmbed(f"Info - {args[0]}", msg, context.author)

        # Adds definition of icons as a new field if actions have been taken:
        if res:
            embed.add_field(name="Total actions taken",
                            value=f"> **{totActions['warn']}** ❗(WARN)\n"
                                  f"> **{totActions['mute']}** 🔇(MUTE)\n"
                                  f"> **{totActions['lockdown']}** 🔒(LOCKDOWN)\n"
                                  f"> **{totActions['kick']}** 🥾(KICK)\n"
                                  f"> **{totActions['ban']}** 🔨(BAN)")
            embed.set_thumbnail(url=args[0].avatar.url)
        await context.channel.send(embed=embed)