from discord.utils import get
from botutils import *

class Lockdown(Command):
    description = ("A lockdown denies a member access to all text and voice channel, except the one made"
                   "specifically for it.\n"
                   "If lockdown is used with no argument, the server enters lockdown mod: this means new members"
                   "will need manual verification to access the server.\n"
                   "If lockdown is used with arguments, its purpose is to remove one user the ability to watch all"
                   "the channels. They will see the not-members channel, which will give them a private chat"
                   "between moderators and themselves.\n"
                   "⚠️ Please note that the lockdown channel is the same for everyone!\n"
                   "The syntax for this command is lockdown <add/remove> <user> <reason (if needed)>\n"
                   "Only ADMINS are allowed to put the server in general lockdown.")
    authorizationLevel = AuthorizationLevel.STAFF
    syntax = [[], [Lexeme.ACTION, Lexeme.USER], [Lexeme.ACTION, Lexeme.USER, Lexeme.TEXT]]

    async def run(self, context, args):
        if len(args) == 0:
            if AuthorizationLevel.getMemberAuthorizationLevel(context.author).value >= AuthorizationLevel.ADMIN.value:
                # General lockdown
                self.bot.updateSetting(['moderation', 'lockdownMode'],
                                       not self.bot.settings['moderation']['lockdownMode']['value'])
                if self.bot.settings['moderation']['lockdownMode']['value']:
                    msg = "🔒 Lockdown mode has been **enabled**!"
                else:
                    msg = "🔓 Lockdown mode has been **disabled**!"
            else:
                msg = "❌ You are not allowed to put the server in general lockdown!"

        else:
            action, user, reason = (args + [None] * 3)[:3]

            memberRoleID = self.bot.settings['moderation']['member']['value']
            if memberRoleID is None:
                msg = "❓ Member role has not been defined! Do it with the settings command first!"
            else:
                # If adding user to lockdown mode:
                if action in COMMAND_ADD:
                    if await self.bot.addModAction(context.author, user, ModActions.LOCKDOWN.value, reason):
                        await user.remove_roles(get(self.bot.guild.roles, id=memberRoleID))
                        msg = "🔒 User has successfuly being lockdown'd!"
                    else:
                        msg = "❗ You are not allowed to lockdown this user!"

                # If removing user from lockdown mode:
                elif action in COMMAND_RM:
                    if AuthorizationLevel.getMemberAuthorizationLevel(
                            context.author).value > AuthorizationLevel.getMemberAuthorizationLevel(user).value:
                        await user.add_roles(get(self.bot.guild.roles, id=memberRoleID))
                        msg = "🔓 User has been removed from lockdown!"
                    else:
                        msg = "❗ You can't remove this user from lockdown mode!"

                # If action not recognized:
                else:
                    msg = f"❓ I didn't understand what you meant by {action}"
        await context.channel.send(msg)