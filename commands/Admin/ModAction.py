from botutils import *
from datetime import datetime
import sqlite3

class ModAction(Command):
    description = (
        "Allows modification of a mod action. This command is used as following: __modaction <ACTION> <ID> (REASON)__."
        "Actions can be view, rm (remove), up (update), or force-rm (force remove).\n"
        "Remove acts as a 'pardon': action will be crossed when using Info command, but still appear just in case.\n"
        "Force remove should be used when mistake was made (misclick, ...), as it completely removes the action from the DB. No reason is needed for that one.\n"
        "Update is used to change the reason (or pardonReason) for an action. If an action has been pardon'd, only the pardon reason can be changed.\n"
        "View is used to get all details about an action.")
    authorizationLevel = AuthorizationLevel.STAFF
    syntax = [[Lexeme.ACTION, Lexeme.INT], [Lexeme.ACTION, Lexeme.INT, Lexeme.TEXT]]

    async def run(self, context, args):
        # Function to remove a mod action. Set force to True to delete it, otherwise updates with pardon.
        def removeAction(action, force=True):
            with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
                cur = con.cursor()
                if force:
                    cur.execute("DELETE FROM mod_log WHERE id = ?", (action['id']))
                else:
                    cur.execute("UPDATE mod_log SET pardon = ?, pardonTimestamp = ?, pardonReason = ? WHERE id = ?",
                                (1, datetime.now(), action['pardonReason'], action['id']))

        # Function to update a mod action.
        def updateAction(action):
            with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
                cur = con.cursor()
                cur.execute("UPDATE mod_log SET reason = ?, pardonReason = ? WHERE id = ?",
                            (action['reason'], action['pardonReason'], action['id']))

        # Function to obtain a mod action in a dict type.
        def getAction(id):
            with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
                cur = con.cursor()
                res = cur.execute("SELECT * FROM mod_log WHERE id = ?", (id,))
                # id, mod, user, action, reason, timestamp, pardon, pardonTimestamp, pardonReason
                res = res.fetchone()

            if not res: return None
            return {"id": res[0], "mod": res[1], "user": res[2], "action": res[3], "reason": res[4],
                    "timestamp": toDateTime(res[5], True), "pardon": res[6],
                    "pardonTimestamp": toDateTime(res[7], True), "pardonReason": res[8]}

        act, actionID = args[0], args[1]
        action = getAction(actionID)
        msg = "⚫ Oops, an unknown error happened!"

        if action is None:
            await context.channel.send(f"❌ I wasn't able to find an action with the ID {actionID}.")
            return

        wrongDoer = await self.bot.fetch_user(action['user'])

        # If moderator is not the one that took action, nor a privileged user:
        if context.author.id != action['mod'] and AuthorizationLevel.getMemberAuthorizationLevel(
                context.author).value < AuthorizationLevel.PRIVILEGED:
            await context.channel.send(f"⚠️ You are not allowed to interact with this action!")
            return

        # If trying to force-remove the action
        if act in ["force-rm", "force", "F", "f", "frm", "force-remove"]:
            if AuthorizationLevel.getMemberAuthorizationLevel(context.author).value >= AuthorizationLevel.PRIVILEGED:
                removeAction(action)  # Force remove the action (default)
                msg = f"✅ <@{action['user']}>s {ModActions(action['action']).name} has been fully deleted!"
            else:
                msg = f"❌ You are not allowed to force-remove an action!"

        # If trying to remove the action
        elif act in COMMAND_RM:
            if len(args) == 3:
                reason = args[2]
            else:
                reason = ""
            action['pardonReason'] = reason
            removeAction(action, False)
            msg = f"✅ <@{action['user']}>s {ModActions(action['action']).name} has been successfully soft-removed!"

        # If trying to update reason of action
        elif act in COMMAND_UPDATE:
            if len(args) == 3:
                reason = args[2]
            else:
                reason = ""

            if action['pardon'] == 1:
                action['pardonReason'] = reason
            else:
                action['reason'] = reason

            updateAction(action)
            msg = f"✅ <@{action['user']}>s {ModActions(action['action']).name} has been successfully updated!"

        # If trying to view the action
        elif act in COMMAND_PREVIEW:
            content = (f"**{ModActions(action['action']).name} - <@{action['user']}>**\n"
                       f"Done <t:{action['timestamp']}:F>\n\n"
                       f"__Reason:__ {action['reason']}")
            if action['pardon'] == 1:
                content += (f"\n`ACTION HAS BEEN PARDON'D at` <t:{action['pardonTimestamp']}:F>\n"
                            f"__Reason:__ {action['pardonReason']}")
            content += f"\n\n__Action taken by:__ <@{action['mod']}>"
            embed = self.bot.getDefaultEmbed(f"Mod Action #{action['id']}", content,
                                             self.bot.guild.get_member(action['mod']))
            embed.set_thumbnail(url=wrongDoer.avatar.url)

            await context.channel.send(embed=embed)
            return

        await context.channel.send(msg)