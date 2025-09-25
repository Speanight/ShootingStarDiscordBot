# MIT Licence
# authors: Luna

import discord
import logging
import random
import requests
from datetime import datetime, timedelta, date
from tokens import SHOOTINGSTAR_TOKEN
from inits import *
from os.path import isfile
import requests
import pytz
import tzlocal
from discord.ext import tasks
from discord.utils import get
import os

from botutils import *


class ShootingStar(Bot):
    ############
    # COMMANDS #
    ############

    class Privilege(Command):
        description = ("Allows to get/add users with privilege for a limited period of time.\n"
                       "__privilege get (all)__ allows you to get current (or all) privileged users.\n"
                       "__privilege add <USER> (minutes [int])__ allows you to give privileges to user for x minutes. Defaults to 5.")
        authorizationLevel = AuthorizationLevel.OWNER
        syntax = [[Lexeme.ACTION, Lexeme.USER], [Lexeme.ACTION, Lexeme.USER, Lexeme.INT], [Lexeme.ACTION, Lexeme.TEXT], [Lexeme.ACTION]]

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
                    await context.channel.send(f"❌ I couldn't privilege <@{user}>, sorry... Was user the owner, or the bot itself?")

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

    class Purge(Command):
        description = "Clears last X messages in the corresponding channel. Defaults to setting value if no number is given."
        authorizationLevel = AuthorizationLevel.STAFF
        syntax = [[], [Lexeme.INT]]

        async def run(self, context, args):
            if not args:
                number = self.bot.settings['defaultValues']['purgeAmount']['value']
            else:
                number = args[0]
            await context.channel.purge(limit=number + 1)

    class Ping(Command):
        description = "Allows you to test connection with me!"
        authorizationLevel = AuthorizationLevel.NONE
        syntax = [[]]

        async def run(self, context, args):
            await context.channel.send("pong")

    class Say(Command):
        description = "Makes me say TEXT in CHANNEL (if specified, otherwise I'll talk in the same one as the one this command has been sent in!)"
        authorizationLevel = AuthorizationLevel.STAFF
        syntax = [[Lexeme.TEXT], [Lexeme.CHANNEL, Lexeme.TEXT]]

        async def run(self, context, args):
            channel = context.channel
            if len(args) == 2: channel = args[0]
            message = args[-1]
            await channel.send(message)

    class Status(Command):
        description = ("Modifies my custom status! No argument (or empty string) to delete it. Gets overwritten by twitch status setting!\n"
                       "If status is equal to refresh and twitch status is activated, refreshes the status of the bot.")
        authorizationLevel = AuthorizationLevel.STAFF
        syntax = [[], [Lexeme.TEXT]]

        async def run(self, context, args):
            if not args:
                message = ""
            elif args[0] == "refresh":
                self.twitchStatus()
            else:
                if not self.bot.settings['twitch']['schedule']['automaticStatus']['value']:
                    if self.bot.updateSetting(['twitch', 'schedule', 'automaticStatus'], True):
                        await context.channel.send(f"✅ Removed automatic status for the twitch channel to display new status!")
                    else:
                        await context.channel.send(f"❌ Couldn't remove automatic status for the twitch channel. Displayed status might get erased soon. Try setting it to False manually with settings command.")
                message = args[0]
            await self.bot.change_presence(activity=discord.Game(name=message))

    class Help(Command):
        description = ("Shows help for commands. Shows every available command if written by itself, otherwise gives a"
                       "quick description if a command name is specified.")
        authorizationLevel = AuthorizationLevel.NONE
        syntax = [[], [Lexeme.TEXT]]

        async def run(self, context, args):
            if not args:
                args = ['General']
                commandsByAuthorization = ["" for _ in
                                           range(AuthorizationLevel.getMemberAuthorizationLevel(
                                               context.author).value + 1)]
                for commands, classes in self.bot.commands.items():
                    if (AuthorizationLevel.getMemberAuthorizationLevel(context.author).value >= getattr(classes,
                                                                                                        "authorizationLevel").value):
                        commandsByAuthorization[
                            getattr(classes, "authorizationLevel").value] += "`" + self.prefix + commands + "`, "
                authorizations = ["None", "Member", "Staff", "Admin", "Privileged", "Owner"]
                msg = ""
                for i in range(len(commandsByAuthorization)):
                    msg += f"```{authorizations[i]}```\n {commandsByAuthorization[i][:-2]}\n"
            else:
                if args[0].lower() in dict(self.bot.commands.items()):
                    command = dict(self.bot.commands.items())[args[0].lower()]
                    desc = getattr(command, 'description').replace('\n', '\n> ')
                    msg = f"> **{self.prefix}{args[0]}** - {desc}\n\n"
                    if (AuthorizationLevel.getMemberAuthorizationLevel(
                            context.author).value >= AuthorizationLevel.STAFF.value):
                        msg += f"__**Authorization needed:**__ {getattr(command, 'authorizationLevel')}\n"
                    syntaxes = '\n'.join(
                        f"- {self.prefix}{args[0]} {syntax}".strip() for syntax in command.getCorrectSyntax())
                    msg += f"\n**Syntaxes:**\n{syntaxes}"
                else:
                    await context.channel.send(
                        f"❌ <@{context.author.id}>, I do not recognize `{args[0]}` as one of my commands!")
                    return

            embed = self.bot.getDefaultEmbed(f"Help - {args[0]}", msg, context.author)
            await context.channel.send(embed=embed)

    class Info(Command):
        description = "Gets moderating info about USER."
        authorizationLevel = AuthorizationLevel.STAFF
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

    class Settings(Command):
        description = f"Gives a quick recap of settings. Values can be modified with <help/add/rm/update> <path/to/setting> <value>."
        authorizationLevel = AuthorizationLevel.PRIVILEGED
        syntax = [[], [Lexeme.ACTION, Lexeme.TEXT], [Lexeme.ACTION, Lexeme.TEXT, Lexeme.TEXT],
                  [Lexeme.ACTION, Lexeme.TEXT, Lexeme.INT], [Lexeme.ACTION, Lexeme.TEXT, Lexeme.USER],
                  [Lexeme.ACTION, Lexeme.TEXT, Lexeme.ROLE], [Lexeme.ACTION, Lexeme.TEXT, Lexeme.BOOL],
                  [Lexeme.ACTION, Lexeme.TEXT, Lexeme.CHANNEL], [Lexeme.ACTION, Lexeme.TEXT, Lexeme.DATE],
                  [Lexeme.ACTION, Lexeme.TEXT, Lexeme.BOOL]]

        async def run(self, context, args):
            def formatValueToStr(v):
                def printType(v):
                    if "value" not in v or "type" not in v:
                        return f"Unknown!"
                    if v["value"] == []:
                        return f"NULL"

                    match type:
                        case "USER":
                            if isinstance(v['value'], list):
                                res = ""
                                for j in v['value']:
                                    res += f"<@{j}>; "
                                return res
                            return f"<@{v['value']}>"
                        case "ROLE":
                            if isinstance(v['value'], list):
                                res = ""
                                for j in v['value']:
                                    res += f"<@&{j}>; "
                                return res
                            return f"<@&{v['value']}>"
                        case "CHANNEL":
                            if isinstance(v['value'], list):
                                res = ""
                                for j in v['value']:
                                    res += f"<#{j}>; "
                                return res
                            return f"<#{v['value']}>"

                    if isinstance(v['value'], list):
                        res = ""
                        for j in v['value']:
                            res += f"{j}; "
                        return res
                    return v['value']

                if "value" not in v or "type" not in v:
                    val = "Unknown!"
                elif v["value"] is None:
                    val = f"NULL"
                else:
                    type = v["type"]
                    isArray = False
                    if type[0] == "!": type = type[1:]
                    if type[0] == "[" and type[-1] == "]":
                        type = type[1:-1]
                        isArray = True
                    val = ""
                    # if isArray and v['value'] != []:
                    #     for i in v['value']:
                    #         val += printType(i)
                    # else:
                    val = printType(v)

                return val

            msg = ""
            if not args:
                for key, value in self.bot.settings.items():
                    msg += f"```{key}```\n"
                    if "value" not in value:
                        for arg, val in value.items():
                            if "value" not in val:
                                msg += f"__**{arg}**__\n"
                                for a, v in val.items():
                                    if a != "secret":
                                        msg += f"- `{a}:` {formatValueToStr(v)}\n"
                                    if a == "secret":
                                        msg += f"- `{a}:` **Secret values won't be displayed on Discord!**\n"
                            else:
                                msg += f"- `{arg}:` {formatValueToStr(val)}\n"
                    else:
                        msg += f"- {formatValueToStr(value)}\n"

                msg += f'\n> If you want to get more details of a setting value, please use {self.prefix}settings <help/add/rm/update> <path/to/setting> "<value>"!'

                embed = self.bot.getDefaultEmbed("Settings", msg, context.author)
                await context.channel.send(embed=embed)
            else:
                action = args[0].lower()
                path = args[1].split("/")
                if action != "help" and len(args) < 3:
                    value = None
                elif action != "help":
                    value = args[2]

                if action == "help":
                    s = self.bot.settings
                    for k in path:
                        if k not in s:
                            await context.channel.send(
                                f"<@{context.author.id}>, I wasn't able to find the setting {' - '.join(path)}!")
                            return
                        s = s[k]
                    msg = ""
                    msg += f"```{' - '.join(path)}```\n> `Current Value:` {s['value']}\n"
                    msg += f"__**Description:**__\n{s['description']}\n\n__Type:__ {s['type']}\n\n"
                    msg += f"> **!** means that the value can be Null, and [] means that the value is an array (and therefor can be changed with add/rm)"
                    embed = self.bot.getDefaultEmbed(f"Settings - Help", msg, context.author)
                    await context.channel.send(embed=embed)
                    return

                if self.bot.updateSetting(path, value):
                    await context.channel.send(
                        f"✅ <@{context.author.id}>, I successfully changed the setting {' - '.join(path)} to {value}!")
                else:
                    await context.channel.send(
                        f"❌ <@{context.author.id}>, I wasn't able to change the setting {' - '.join(path)} to {value}!")

    ###################
    # TWITCH COMMANDS #
    ###################
    class Twitch(Command):
        description = "Outputs the current Twitch channel checked by the bot"
        authorizationLevel = AuthorizationLevel.MEMBER
        syntax = [[]]

        async def run(self, context, args):
            # Recovers Twitch channel ID
            id = self.bot.settings['twitch']['channel']['value']
            if id is None:
                # If Twich channel not setup...
                await context.channel.send(f"❗ No twitch channel is being monitored right now!")
                return
            token = self.bot.getTwitchToken()

            # Otherwise, get all details about twitch channel.
            response = requests.get(
                f"https://api.twitch.tv/helix/users?id={id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "client-id": f"{self.bot.settings['twitch']['OAuth']['id']['value']}"
                }
            )
            res = response.json()['data'][0]

            # And add everything to an embed.
            embed = discord.Embed(title=res['display_name'],
                                  url=f"https://twitch.tv/{res['login']}",
                                  description=f"> {res['description']}\n\n**Status:** {res['broadcaster_type']}",
                                  colour=0xa748c3,
                                  timestamp=datetime.now())
            embed.set_author(name="Twitch Channel")
            embed.set_image(url=res['offline_image_url'])
            embed.set_thumbnail(url=res['profile_image_url'])
            embed.set_footer(text=f"Version {VERSION}", icon_url="attachment://BotPFP.png")

            await context.channel.send(embed=embed)

    class Schedule(Command):
        description = ("Gives the next planned streams of da purple pegasi! You can override default values and specify"
                       "amount of streams to display (1-25), or if you only want the streams of current week or not"
                       "(false/true)")
        authorizationLevel = AuthorizationLevel.MEMBER
        syntax = [[], [Lexeme.INT], [Lexeme.BOOL]]

        async def run(self, context, args):
            maxLimit = self.bot.settings['twitch']['schedule']['maxLimit']['value']
            perWeek = self.bot.settings['twitch']['schedule']['perWeek']['value']

            if maxLimit > 25: maxLimit = 25

            if len(args) == 1:
                # User specified to show per week.
                if isinstance(args[0], bool):
                    perWeek = args[0]
                    maxLimit = 25 # Maximum imposed by Twitch.

                # Specified amount of streams to show.
                elif isinstance(args[0], int):
                    if 1 < args[0] < 25:
                        maxLimit = args[0]
                        perWeek = False # Disables per week view to display amount of stream requested (if applicable)


            token = self.bot.getTwitchToken()
            if token is None:
                await context.channel.send(f"❌ No twitch OAuth token is being used. Please set them in settings.")
            if self.bot.settings['twitch']['channel']['value'] is None:
                await context.channel.send(f"❌ No twitch channel is being monitored right now!")
                return
            response = requests.get(
                f"https://api.twitch.tv/helix/users?id={self.bot.settings['twitch']['channel']['value']}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "client-id": f"{self.bot.settings['twitch']['OAuth']['id']['value']}"
                }
            )
            user = response.json()['data'][0]

            response = requests.get(
                f"https://api.twitch.tv/helix/schedule?broadcaster_id={self.bot.settings['twitch']['channel']['value']}&first={maxLimit}",
                headers = {
                    "Client-ID": self.bot.settings['twitch']['OAuth']['id']['value'],
                    "Authorization": f"Bearer {token}"
                }
            )
            schedule = response.json()['data']
            msg = ""

            if schedule['vacation'] is None or int(self.bot.getDateTime(schedule['vacation']['end_time']).timestamp()) < int(datetime.now().timestamp()):
                for i in schedule['segments']:
                    if not perWeek or int(self.bot.getDateTime(i['start_time']).timestamp()) < (datetime.now() + timedelta(days=(7 - datetime.now().weekday()))).replace(hour=0, minute=0, second=0, microsecond=0).timestamp():
                        msg += '- '
                        if i['is_recurring']: msg += '🔁'
                        msg += f"<t:{int(self.bot.getDateTime(i['start_time']).timestamp())}:f> | **{i['category']['name']}**: {i['title']}\n"
            else:
                msg = f"{user['display_name']} is in **Vacation** right now!\nThey will return with awesome content starting <t:{int(self.bot.getDateTime(schedule['vacation']['end_time']).timestamp())}:F>!"

            author = "Twitch Schedule - "
            if perWeek: author += "Week schedule"
            else: author += f"{maxLimit} next streams"

            # And add everything to an embed.
            embed = discord.Embed(title=user['display_name'],
                                  url=f"https://twitch.tv/{user['login']}",
                                  description=msg,
                                  colour=0xa748c3,
                                  timestamp=datetime.now())
            embed.set_author(name=author)
            embed.set_thumbnail(url=user['profile_image_url'])
            if schedule['vacation'] is not None: embed.set_image(url=user['offline_image_url'])
            embed.set_footer(text=f"Version {VERSION}", icon_url="attachment://BotPFP.png")

            await context.channel.send(embed=embed)

    ###############
    # MOD ACTIONS #
    ###############
    class Mute(Command):
        description = ("Mutes a user for specified time and reason\n"
                       "Quick reminder that a 'duration' should be used with this syntax: 1d2h3m to mute the user"
                       "for one day, two hours and three minutes.")
        authorizationLevel = AuthorizationLevel.STAFF
        syntax = [[Lexeme.USER], [Lexeme.USER, Lexeme.DURATION], [Lexeme.USER, Lexeme.TEXT, Lexeme.DURATION], [Lexeme.USER, Lexeme.DURATION, Lexeme.TEXT]]

        async def run(self, context, args):
            if self.bot.settings['moderation']['muted']['value'] is None:
                await context.channel.send("❗ No muted role has been attributed. Therefor, mutes are unavailable. Please ask owner or privileged to set it with settings command.")
                return
            user, reason = args[0], ""
            time = {"days": 0, "hours": 0, "minutes": self.bot.settings['defaultValues']['muteTime']['value']}
            if len(args) >= 2:
                if type(args[1]) is dict: time = args[1]
                else: reason = args[1]

                if len(args) == 3:
                    if type(args[2]) is dict: time = args[2]
                    else: reason = args[2]

            id = self.bot.addModAction(context.author, user, ModActions.MUTE.value, reason + f" | {time['days']}d{time['hours']}h{time['minutes']}m")
            if id is not False:
                modactions = self.bot.readJSONFrom('jsons/modactions.json')
                pardon = datetime.now() + timedelta(days=time['days'], hours=time['hours'], minutes=time['minutes'])
                if modactions == {}: modactions = []
                modactions.append({"id": id, "user": user.id, "pardon": pardon.timestamp(), "action": ModActions.MUTE.value})
                self.bot.writeJSONTo('jsons/modactions.json', modactions)

                if len(modactions) == 1:
                    print(f"Starting modActionsPardon!")
                    await self.bot.modActionPardon()

                await user.add_roles(get(self.bot.guild.roles, id=self.bot.settings['moderation']['muted']['value']))
                await context.channel.send(f"{user.display_name} has been muted for {time['days']}d{time['hours']}h{time['minutes']}m!")

    class Unmute(Command):
        description = "Unmutes an user if that user was muted before. This will remove any pending duration."
        authorizationLevel = AuthorizationLevel.STAFF
        syntax = [[Lexeme.USER]]

        async def run(self, context, args):
            if self.bot.settings['moderation']['muted']['value'] is None:
                await context.channel.send("❗ No muted role has been attributed. Therefor, mutes are unavailable. Please ask owner or privileged to set it with settings command.")
                return

            user, id = args[0], None

            modactions = self.bot.readJSONFrom('jsons/modactions.json')
            for i in modactions:
                if i['user'] == user.id:
                    id = i['id']
                    modactions.remove(i)
            if id is not None:
                self.bot.writeJSONTo('jsons/modactions.json', modactions)

            if AuthorizationLevel.getMemberAuthorizationLevel(context.author).value > AuthorizationLevel.getMemberAuthorizationLevel(user).value:
                msg = "✅ The user has been unmuted."
                await user.remove_roles(get(self.bot.guild.roles, id=self.bot.settings['moderation']['muted']['value']))
            else:
                msg = "❌ You are not allowed to unmute this user."

            await context.channel.send(msg)

    class Warn(Command):
        description = "Warns user for specified reason (if specified)"
        authorizationLevel = AuthorizationLevel.STAFF
        syntax = [[Lexeme.USER], [Lexeme.USER, Lexeme.TEXT]]

        async def run(self, context, args):
            if len(args) == 2: reason = args[1]
            else: reason = ""

            if self.bot.addModAction(context.author, args[0], ModActions.WARN.value, reason):
                await context.channel.send(f"{args[0].display_name} has been successfully warned!")
            else:
                await context.channel.send(f"You are not allowed to take action on this user!")

    class Kick(Command):
        description = "Kicks USER from server, with given reason - if specified."
        authorizationLevel = AuthorizationLevel.STAFF
        syntax = [[Lexeme.USER], [Lexeme.USER, Lexeme.TEXT]]

        async def run(self, context, args):
            user = args[0]
            if len(args) == 1: reason = ""
            else: reason = args[1]

            try:
                await user.kick(reason=reason)
                if self.bot.addModAction(context.author, user, ModActions.KICK.value, reason):
                    await context.channel.send(f"{args[0].display_name} has been successfully kicked!")
                    logChannel = self.bot.settings['logs']['channel']['value']
                    if logChannel is None: return
                    embed = self.bot.getDefaultEmbed("User kick",
                                                     f"{user.name} has been kicked by {context.author.name}, with reason {reason}",
                                                     context.author, 0xff0000)
                    await logChannel.send(embed=embed)

                else:
                    await context.channel.send(f"You are not allowed to take action on this user!")
            except discord.errors.Forbidden:
                await context.channel.send(f'`Kick error: impossible to kick user {user.name}`')

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
                    self.bot.updateSetting(['moderation', 'lockdownMode'], not self.bot.settings['moderation']['lockdownMode']['value'])
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
                        if self.bot.addModAction(context.author, user, ModActions.LOCKDOWN.value, reason):
                            await user.remove_roles(get(self.bot.guild.roles, id=memberRoleID))
                            msg = "🔒 User has successfuly being lockdown'd!"
                        else:
                            msg = "❗ You are not allowed to lockdown this user!"

                    # If removing user from lockdown mode:
                    elif action in COMMAND_RM:
                        if AuthorizationLevel.getMemberAuthorizationLevel(context.author).value > AuthorizationLevel.getMemberAuthorizationLevel(user).value:
                            await user.add_roles(get(self.bot.guild.roles, id=memberRoleID))
                            msg = "🔓 User has been removed from lockdown!"
                        else:
                            msg = "❗ You can't remove this user from lockdown mode!"

                    # If action not recognized:
                    else:
                        msg = f"❓ I didn't understand what you meant by {action}"
            await context.channel.send(msg)

    class Ban(Command):
        description = ("Bans USER from server with given reason - if specified - and deletes the messages sent by them"
                       "in the last X (max. 7) days.\n"
                       "You may also temporarily ban a user by typing a duration."
                       "(ie: 1d2h3m bans for 1 days, 2 hours and 3 minutes)\n"
                       "__Except 'user', none of the arguments are required.__ Correct syntaxes are following:"
                       "ban <user> <reason> <duration> <deleteTime>\n")
        authorizationLevel = AuthorizationLevel.ADMIN
        syntax = [[Lexeme.USER], [Lexeme.USER, Lexeme.TEXT], [Lexeme.USER, Lexeme.TEXT, Lexeme.DURATION], [Lexeme.USER, Lexeme.TEXT, Lexeme.DURATION, Lexeme.INT]]

        async def run(self, context, args):
            user, reason, duration, deleteTime = (args + [None] * 4)[:4]

            if deleteTime is not None: reason += f" - messages over the last {deleteTime} days have been deleted"
            else: deleteTime = 0
            try:
                id = self.bot.addModAction(context.author, user, ModActions.BAN.value, reason)
                if id is not False:
                    await user.ban(reason=reason, delete_message_days=deleteTime)
                    await context.channel.send(f"✅ {args[0].display_name} has been successfully banned!")
                    if duration is not None:
                        modactions = self.bot.readJSONFrom('jsons/modactions.json')
                        pardon = datetime.now() + timedelta(days=duration['days'], hours=duration['hours'],
                                                            minutes=duration['minutes'])
                        if modactions == {}: modactions = []
                        modactions.append(
                            {"id": id, "user": user.id, "pardon": pardon.timestamp(), "action": ModActions.BAN.value})
                        self.bot.writeJSONTo('jsons/modactions.json', modactions)
                        if len(modactions) == 1:
                            self.bot.modActionPardon.start()
                else:
                    await context.channel.send(f"❌ The ban couldn't be done. Perhaps the user has higher authorization than you?")
            except discord.errors.Forbidden:
                await context.channel.send(f'❌ `Ban error: impossible to ban user {user.name}`')

    class ModAction(Command):
        description = ("Allows modification of a mod action. This command is used as following: __modaction <ACTION> <ID> (REASON)__."
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
                return {"id": res[0], "mod": res[1], "user": res[2], "action": res[3], "reason": res[4], "timestamp": toDateTime(res[5], True), "pardon": res[6], "pardonTimestamp": toDateTime(res[7], True), "pardonReason": res[8]}

            act, actionID = args[0], args[1]
            action = getAction(actionID)
            msg = "⚫ Oops, an unknown error happened!"

            if action is None:
                await context.channel.send(f"❌ I wasn't able to find an action with the ID {actionID}.")
                return

            wrongDoer = await self.bot.fetch_user(action['user'])

            # If moderator is not the one that took action, nor a privileged user:
            if context.author.id != action['mod'] and AuthorizationLevel.getMemberAuthorizationLevel(context.author).value < AuthorizationLevel.PRIVILEGED:
                await context.channel.send(f"⚠️ You are not allowed to interact with this action!")
                return

            # If trying to force-remove the action
            if act in ["force-rm", "force", "F", "f", "frm", "force-remove"]:
                if AuthorizationLevel.getMemberAuthorizationLevel(context.author).value >= AuthorizationLevel.PRIVILEGED:
                    removeAction(action) # Force remove the action (default)
                    msg = f"✅ <@{action['user']}>s {ModActions(action['action']).name} has been fully deleted!"
                else:
                    msg = f"❌ You are not allowed to force-remove an action!"

            # If trying to remove the action
            elif act in COMMAND_RM:
                if len(args) == 3: reason = args[2]
                else: reason = ""
                action['pardonReason'] = reason
                removeAction(action, False)
                msg = f"✅ <@{action['user']}>s {ModActions(action['action']).name} has been successfully soft-removed!"

            # If trying to update reason of action
            elif act in COMMAND_UPDATE:
                if len(args) == 3: reason = args[2]
                else: reason = ""

                if action['pardon'] == 1: action['pardonReason'] = reason
                else: action['reason'] = reason

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
                embed = self.bot.getDefaultEmbed(f"Mod Action #{action['id']}", content, self.bot.guild.get_member(action['mod']))
                embed.set_thumbnail(url=wrongDoer.avatar.url)

                await context.channel.send(embed=embed)
                return

            await context.channel.send(msg)

    class Uptime(Command):
        description = "Shows how long Shooting Star has been online for."
        authorizationLevel = AuthorizationLevel.STAFF
        syntax = [[]]

        async def run(self, context, args):
            startTime = self.bot.startTime.strftime('%d/%m/%Y %H:%M')
            uptime = datetime.now() - self.bot.startTime
            await context.channel.send(f"I'm awake since {startTime}.\nMy current uptime is {uptime.days} day(s).")

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


                msg = {'id': len(plannedMsg)+1, 'channel': channel.id, 'time': int(day.timestamp()), 'msg': content, 'embed': attach}
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


    ##################
    # "FUN" COMMANDS #
    ##################
    class Birthday(Command):
        description = ("Shooting Star can wish you happy birthday! Add your birthday with __!birthday add DD/MM__ (or DD/MM/YYYY if you want her to know your age too!)\n"
                       "If you want to show the next X birthdays, you just have to type __!birthday X__ (or without argument to show the next few ones)!\n"
                       "She can also forget your birthday with __!birthday remove__")
        authorizationLevel = AuthorizationLevel.MEMBER
        syntax = [[], [Lexeme.INT], [Lexeme.ACTION, Lexeme.DATE], [Lexeme.ACTION]]

        async def run(self, context, args):
            msg, embed = None, None

            def getNextBirthdays(limit):
                def getNextOccurence(rawDate):
                    bdayDay = datetime.strptime(rawDate[0:10], '%Y-%m-%d')
                    now = datetime.now()

                    if now < bdayDay: bdayDay = bdayDay.replace(year=now.year)
                    else: bdayDay = bdayDay.replace(year=now.year+1)

                    return bdayDay + timedelta(hours=14)

                if limit > 20: limit = 20
                # Display the next X birthday
                with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
                    cur = con.cursor()
                    res = cur.execute(f"select user, day, julianday(strftime('%Y', 'now')||strftime('-%m-%d', day))-julianday('now') as birthday from birthday LIMIT {limit}")
                    res = res.fetchall()

                    if not res:
                        return self.bot.getDefaultEmbed("Incoming birthdays", f"❓ I don't know the birthday of anyone here! You can add yours by typing birthday add DD/MM!", context.author)

                    msg = ""
                    for i in res:
                        date = getNextOccurence(i[1])

                        entry = {"user": f"<@{i[0]}>", "bday": date}
                        if entry['bday'].month == datetime.now().month and entry['bday'].day == datetime.now().day:
                            msg += f"> {entry['user']} | 🎂 TODAY! WISH THEM HAPPY BDAY!\n"
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
                if len(args) == 0: limit = 10
                else: limit = args[0]
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

    class Eightball(Command):
        description = "8ball command: asks it anything, and it shall give you THE answer (definitely not something random trust)"
        authorizationLevel = AuthorizationLevel.MEMBER
        syntax = [[Lexeme.TEXT]]

        async def run(self, context, args):
            answers = ["Definitely!", "Yes!", "Most likely.", "As I see it, yes", "Signs point to yes.", "Yes.",
                       "Ask again later", "Better keep that secret...", "I'm not sure",
                       "Nuh-uh!", "No", "Nope!", "Very doubtful", "No way!", "Impossible."]
            random.seed(datetime.now().timestamp())
            await context.channel.send(random.choice(answers))

    class Cute(Command):
        description = "Gives your daily cute % if used without argument."
        authorizationLevel = AuthorizationLevel.MEMBER
        syntax = [[]]

        async def run(self, context, args):
            def getCutePercentage(seed):
                random.seed(seed)
                return random.random() * 100

            # Using cute %age command
            if not args:
                today = datetime.now()
                today = today.replace(hour=0, minute=0, second=0, microsecond=0)
                percent = round(getCutePercentage(context.author.id + today.timestamp()), 2)

                await context.channel.send(f"<@{context.author.id}>, you are **{percent}%** cute today!")

    # class Quote(Command):
    #     description = ('Allows you to add, list or get details of a quote.\n'
    #                    'To add a quote, use !quote add <@user> "quote".\n'
    #                    'To list quotes, just use !quote\n'
    #                    'To get details of a quote, use !quote get <QuoteID>.')
    #     authorizationLevel = AuthorizationLevel.MEMBER
    #     syntax = [[], [Lexeme.ACTION, Lexeme.USER, Lexeme.TEXT], [Lexeme.ACTION, Lexeme.INT]]
    #
    #     async def run(self, context, args):
    #         pass


    ################
    # LOOPED TASKS #
    ################
    # Checks if a message needs to be sent in a channel.
    @tasks.loop(minutes=1)
    async def messagePlanner(self):
        msg = self.readJSONFrom('jsons/plannedMessages.json')
        newMsg = []
        now = datetime.now().timestamp()
        for i in msg:
            if now > i['time']:
                try:
                    channel = self.get_channel(i['channel'])
                    if len(i['embed']) > 0:
                        file = discord.File(f"files/{i['embed'][0]}")
                        await channel.send(i['msg'], file=file)
                        os.remove(f"files/{i['embed'][0]}")
                    else:
                        await channel.send(i['msg'])
                except Exception as e:
                    print(f"Failed to send message {i['id']}! Error: {e}")
                    newMsg.append(i)
            else:
                newMsg.append(i)

        if not newMsg:
            print(f"Stopping messagePlanner execution...")
            self.messagePlanner.stop()
        self.writeJSONTo('jsons/plannedMessages.json', newMsg)

    @tasks.loop(minutes=1)
    async def modActionPardon(self):
        actions = self.readJSONFrom('jsons/modactions.json')
        newActions = []
        now = datetime.now().timestamp()
        if not actions:
            print(f"Stopping modActionPardon execution...")
            self.modActionPardon.stop()
        for i in actions:
            if now > i['pardon']:
                if i['action'] == ModActions.MUTE.value:
                    user = self.guild.get_member(i['user'])
                    await user.remove_roles(get(self.guild.roles, id=self.settings['moderation']['muted']['value']))

                if i['action'] == ModActions.BAN.value:
                    user = await self.fetch_user(i['user'])
                    await self.guild.unban(user)

            else:
                newActions.append(i)

        self.writeJSONTo('jsons/modactions.json', newActions)


    # TODO: https://discordpy.readthedocs.io/en/stable/api.html?highlight=reaction#discord.on_reaction_add
    # Checks twitch status.
    @tasks.loop(minutes=10)
    async def twitchStatus(self):
        updateStatus = self.settings['twitch']['schedule']['automaticStatus']['value']
        id = self.settings['twitch']['channel']['value']

        if updateStatus and id is not None:
            print("Updating status...")
            # Recovering data with Twitch API
            token = self.getTwitchToken()
            response = requests.get(
                f"https://api.twitch.tv/helix/schedule?broadcaster_id={self.settings['twitch']['channel']['value']}&first=1",
                headers={
                    "Client-ID": self.settings['twitch']['OAuth']['id']['value'],
                    "Authorization": f"Bearer {token}"
                }
            )
            schedule = response.json()['data']

            response = requests.get(
                f"https://api.twitch.tv/helix/streams?user_id={self.settings['twitch']['channel']['value']}",
                headers={
                    "Client-ID": self.settings['twitch']['OAuth']['id']['value'],
                    "Authorization": f"Bearer {token}"
                }
            )
            stream = response.json()['data']

            print("Twitch API done!")
            print(f"Stream: {stream}")
            print(f"Schedule: {schedule}")

            # If streamer is on vacation:
            if schedule['vacation'] is not None and ('end_time' in schedule['vacation'] and int(
                    self.getDateTime(schedule['vacation']['end_time']).timestamp()) > int(datetime.now().timestamp())):
                status = discord.Status.dnd
                activity = discord.CustomActivity(
                    name=f"In vacation! Back the {self.getDateTime(schedule['vacation']['end_time']).strftime('%d %B')}",
                    emoji="☀️")
                self.twitchStatus.change_interval(hours=24)

            # Otherwise, if live right now:
            elif stream:
                stream = stream[0]
                status = discord.Status.online
                activity = discord.Streaming(platform="Twitch", url=f"https://twitch.tv/{stream['user_login']}",
                                           twitch_name=stream['user_login'], name=stream['title'], game=stream['game_name'])
                self.twitchStatus.change_interval(minutes=5)

            # Otherwise: if a stream is planned:
            elif schedule['segments']:
                status = discord.Status.online
                activity = discord.CustomActivity(
                    name=f"Next stream planned {self.getDateTime(schedule['segments'][0]['start_time'], True).strftime('%d/%m %H:%M')} UTC")
                self.twitchStatus.change_interval(hours=1)

            # Otherwise: if no stream is planned:
            else:
                print("No stream planned...")
                status = discord.Status.idle
                activity = discord.CustomActivity(name=f"No stream planned! (yet!)", emoji="⏰")
                self.twitchStatus.change_interval(hours=12)

            print(f"Updating status...")

            await self.change_presence(status=status, activity=activity)

    #######################
    # ON MESSAGE RECEIVED #
    #######################

    async def on_message(self, message):
        await self.wait_until_ready()
        # Snow Pearl doesn't answer to its own messages or empty messages
        if message.author == self.user or message.content == "": return

        # is message trying to call an existing command?
        cmd = self.getCommand(message)
        if cmd is not None:
            await cmd.ParseAndTrySafeRun(self, message)

        # For custom reactions to messages, add else: condition and check message content.

    ####################
    # EVENT FUNCTIONS  #
    ####################

    async def on_ready(self):
        await super().on_ready()
        self.guild = self.guilds[0]
        print(f'Server: {self.guild.name}.')
        if not isfile(f"{DB_FOLDER}{self.guild.id}"):
            print(f"Creating DB...")
            initDB(self.guild.id)
        print("Checking settings...")
        initSettings()
        self.settings = self.readJSONFrom('jsons/settings.json')
        print("Checking if owner is in settings...")
        if self.settings['moderation']['owner']['value'] is None:
            print("It is: replacing None to owner ID...")
            self.settings['moderation']['owner']['value'] = self.guild.owner.id
            self.writeJSONTo('jsons/settings.json', self.settings)
        print(f"Writing guild ID in utils.json...")
        utils = self.readJSONFrom('jsons/utils.json')
        utils['guildID'] = self.guild.id
        self.writeJSONTo('jsons/utils.json', utils)
        self.silent_logs = self.settings['logs']['channel']['value']

        print(f'Starting repeated tasks...')
        self.messagePlanner.start()
        self.modActionPardon.start()
        print(f'Ready!')

        self.twitchStatus.start()

    async def on_member_join(self, member):
        # Add the member role
        if self.settings['newcomers']['roles']['value'] is not []:
            for role in self.settings['newcomers']['roles']['value']:
                try:
                    await member.add_roles(discord.utils.get(member.guild.roles, id=role))
                except discord.Forbidden:
                    pass

        if self.settings['moderation']['member']['value'] is not None and self.settings['moderation']['lockdownMode']['value'] is False:
            try:
                await member.add_roles(discord.utils.get(member.guild.roles, id=self.settings['moderation']['member']['value']))
            except discord.Forbidden:
                pass

        embed = discord.Embed(title="User joined", color=discord.Colour.green(),
                              description=f"User **{member.name}** joined the server.\nAccount created the: {member.created_at.day}/{member.created_at.month}/{member.created_at.year}")
        # embed.set_thumbnail(url="attachment://icon_join.png")
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")
        # await self.silent_logs.send(file=discord.File("images/icon_join.png"), embed=embed)

        # await self.silent_logs.send(embed=embed)

    async def on_member_remove(self, member):
        embed = discord.Embed(title="User left", color=discord.Colour.red(),
                              description=f"User **{member.name}** left the server")
        # embed.set_thumbnail(url="attachment://icon_join.png")
        embed.set_footer(text=f"User ID: {member.id}")

    async def on_member_update(self, member_old, member_new):
        if member_old.display_name != member_new.display_name:
            embed = discord.Embed(title="User updated", color=discord.Colour.gold(),
                                  description=f"User **{member_new.name}** changed their username.\nChange: {member_old.display_name} -> {member_new.display_name}")
            embed.set_thumbnail(url="attachment://icon_update.png")
            embed.set_footer(text=f"User ID: {member_new.id}")

    ####################
    # USEFUL FUNCTIONS #
    ####################

    # send a list of string in channel as separate messages. Messages starting with ./images/ are treated like files
    async def send_all(self, channel, texts):
        for text in texts:
            if text.startswith("./images/"):
                try:
                    with open(text, 'rb') as file:
                        await channel.send(file=discord.File(file))
                except FileNotFoundError:
                    continue
            else:
                await channel.send(text)

    # returns true iif all elements in l are in content
    def all_in(self, content, l):
        return all([True if element in content else False for element in l])

    # returns true if any element in l is in content
    def any_in(self, content, l):
        return any([True if element in content else False for element in l])


if __name__ == "__main__":
    star = ShootingStar()
    star.run(SHOOTINGSTAR_TOKEN, log_handler=logging.FileHandler(filename='shootingstar.log', encoding='utf-8',
                                                                 mode='w')) #, log_level=logging.DEBUG)
