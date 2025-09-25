# MIT Licence
# authors: Luna and Yashn

WARNS_FILE = "jsons/warns.json"
BIRTHDAYS_FILE = "jsons/birthdays.json"
PRIVILEGED_FILE = "jsons/privileged.json"
DB_FOLDER = 'db/'
VERSION = "1.0.1"

##### COMMANDS UTILS #####
COMMAND_ADD = ["add", "adds", "new", "+"]
COMMAND_RM = ["remove", "rm", "rem", "delete", "del", "-"]
COMMAND_LIST = ["list", "ls", "="]
COMMAND_PREVIEW = ["preview", "view", "watch", "see", "pv", "pw", "info", "?"]
COMMAND_UPDATE = ["update", "up", "#"]

# import logging
import discord
import discord.utils
import inspect
from enum import Enum
from os.path import isfile
from datetime import datetime, timezone
import json
from tokens import *
import sqlite3
import requests
import time
import tzlocal
import pytz
import re


class ModActions(Enum):
    WARN = 1
    MUTE = 2
    KICK = 3
    BAN = 4
    LOCKDOWN = 5

    def __repr__(self):
        return str(self.name)


class AuthorizationLevel(Enum):
    # Roles ID
    NONE = 0
    MEMBER = 1
    STAFF = 2
    ADMIN = 3
    PRIVILEGED = 4
    OWNER = 5

    def __repr__(self):
        return str(self.name)

    @staticmethod
    def getMemberAuthorizationLevel(member):
        # Gets list of current privileged.
        privileged = getPrivileged(None, True)
        privileges = []
        for i in privileged: privileges.append(i['user'])

        # Getting IDs in settings:
        if not isfile('jsons/settings.json'):
            settings = json.loads("{}")
        else:
            settings = json.loads(open('jsons/settings.json', 'r').read())

        owner_id = settings['moderation']['owner']['value']
        admin_role_id = settings['moderation']['admin']['value']
        staff_role_id = settings['moderation']['staff']['value']
        member_role_id = settings['moderation']['member']['value']

        roles = [role.id for role in member.roles]
        if member.id == owner_id: return AuthorizationLevel.OWNER
        if member.id in privileges:
            return AuthorizationLevel.PRIVILEGED
        elif admin_role_id in roles:
            return AuthorizationLevel.ADMIN
        elif staff_role_id in roles:
            return AuthorizationLevel.STAFF
        elif member_role_id in roles:
            return AuthorizationLevel.MEMBER
        else:
            return AuthorizationLevel.NONE


class Lexeme(Enum):
    TEXT = 1
    USER = 2
    ROLE = 3
    CHANNEL = 4
    INT = 5
    COMMAND = 6
    DATE = 7
    DATETIME = 8
    DURATION = 9
    BOOL = 10
    ACTION = 11

    def __repr__(self):
        return str(self.name)

    def from_string(self, name):
        try:
            return self[name]
        except KeyError:
            raise ValueError(f"Unknown Lexeme type: {name}")


class Context:
    def __init__(self, author, channel, message):
        self.author = author
        self.channel = channel
        self.message = message


class Command:
    prefix = "!"

    def getCorrectSyntax(self):
        syntaxes = []
        for syn in self.syntax:
            syntaxes.append(' '.join(repr(lexeme) for lexeme in syn))
        return syntaxes

    @staticmethod
    def TryParseDate(s):
        formats = ['%d/%m', '%d/%m/%Y']
        for format in formats:
            try:
                return datetime.strptime(s, format)
            except ValueError:
                continue
        return None

    @staticmethod
    def TryParseDateTime(s):
        formats = ['%d/%m/%Y.%H:%M', '%d/%m/%Y-%H:%M']
        for format in formats:
            try:
                return datetime.strptime(s, format)
            except ValueError:
                continue
        return None

    def lexemize(self, message):
        QUOTES = ("\"", "„", "”", "“", "”", "'")
        parsedInput, lexemes = [], []

        splitedMessage = message.content.split(" ")
        isInMessage = False

        for eword, word in enumerate(splitedMessage):
            # end of message with " at the end (not \"): add message to parsed data and removes the " at the end
            if isInMessage and not word.endswith("\\\"") and word.endswith(QUOTES):
                isInMessage = False
                parsedInput[-1].append(word[:-1])
                parsedInput[-1] = " ".join(parsedInput[-1])
            # inside a message which is not over
            elif isInMessage:
                parsedInput[-1].append(word)
            # starts of a message with "
            elif not isInMessage and word.startswith(QUOTES) and (not word.endswith(QUOTES) or word.endswith("\\\"")):
                isInMessage = True
                parsedInput.append([word[1:]])
                lexemes.append(Lexeme.TEXT)
            # first word starts with !: command
            elif eword == 0 and word.startswith(Command.prefix):
                parsedInput.append(word)
                lexemes.append(Lexeme.COMMAND)
            # int
            elif word.isnumeric():
                parsedInput.append(int(word))
                lexemes.append(Lexeme.INT)
            elif Command.TryParseDate(word) != None:
                parsedInput.append(Command.TryParseDate(word))
                lexemes.append(Lexeme.DATE)
            elif Command.TryParseDateTime(word) != None:
                parsedInput.append(Command.TryParseDateTime(word))
                lexemes.append(Lexeme.DATETIME)
            # role, mention or channel
            elif word.startswith("<@&") and word[3:-1].isnumeric() and word.endswith(">"):
                parsedInput.append(int(word[3:-1]))
                lexemes.append(Lexeme.ROLE)
            elif word.startswith("<@") and word[2:-1].isnumeric() and word.endswith(">"):
                parsedInput.append(int(word[2:-1]))
                lexemes.append(Lexeme.USER)
            elif word.startswith("<#") and word[2:-1].isnumeric() and word.endswith(">"):
                parsedInput.append(int(word[2:-1]))
                lexemes.append(Lexeme.CHANNEL)

            # Action
            elif word in COMMAND_ADD or word in COMMAND_RM or word in COMMAND_LIST or word in COMMAND_PREVIEW or word in COMMAND_UPDATE:
                parsedInput.append(word)
                lexemes.append(Lexeme.ACTION)
            # empty message
            elif word == "\"\"":
                parsedInput.append("")
                lexemes.append(Lexeme.TEXT)
            # we check everything else: it's just a word
            else:
                # If word is "true" or "false": it's a bool
                if word == "true" or word == "false":
                    parsedInput.append(word == "true")
                    lexemes.append(Lexeme.BOOL)
                else:
                    # We check to see if the word is actually a duration
                    matches = re.findall(r'(\d+)([dhm])', word)
                    result = {"days": 0, "hours": 0, "minutes": 0}
                    for value, unit in matches:
                        value = int(value)
                        if unit == "d": result['days'] += value
                        if unit == "h": result['hours'] += value
                        if unit == "m": result['minutes'] += value
                    if result["days"] != 0 or result["hours"] != 0 or result["minutes"] != 0:
                        parsedInput.append(result)
                        lexemes.append(Lexeme.DURATION)
                    else:
                        # Else, it's just a word.
                        if word.startswith(QUOTES) and word.endswith(QUOTES):
                            word = word[1:-1]
                        parsedInput.append(word)
                        lexemes.append(Lexeme.TEXT)

        # if isInMessage is True, then a closing " is missing: parsing failed!
        if isInMessage: return None, None
        return parsedInput, lexemes

    # parse and call it if no syntax error, else prints correct command syntax
    async def ParseAndTrySafeRun(self, bot, message):
        # PARSING
        # parsing step
        parsedInput, lexemes = self.lexemize(message)
        # if parsing or syntax check fail: stop here and print correct command's syntax
        if parsedInput is None or lexemes[1:] not in self.syntax:
            await message.channel.send(
                f"`Syntaxes:`\n" +
                "\n".join(
                    f"{self.prefix}{self.__class__.__name__.lower()} {syntax}" for syntax in self.getCorrectSyntax()))
            return

        # CHECK AND CONVERT
        # everything should be safe on a lexical point of view here
        # convert and check role/user/channel ID in role/mention/channel lexemes for safe and easier laster use then run command
        for item in range(len(lexemes)):
            # is mentioned role existing on the guild?
            if lexemes[item] == Lexeme.ROLE:
                if message.guild.get_role(parsedInput[item]) != None:
                    parsedInput[item] = message.guild.get_role(parsedInput[item])
                else:
                    await message.channel.send(
                        f"`Invalid role: role <@&{parsedInput[item]}> does not exists on this server`")
                    return
            # is mentioned user part of the guild?
            if lexemes[item] == Lexeme.USER:
                if message.guild.get_member(parsedInput[item]) is not None:
                    # parsedInput[item] = bot.get_user(parsedInput[item])
                    parsedInput[item] = bot.guild.get_member(parsedInput[item])
                else:
                    parsedInput[item] = await bot.fetch_user(parsedInput[item])
                    # await message.channel.send(f"`Invalid user: user <@{parsedInput[item]}> is not on this server`")
                    # return
            # is mentioned channel existing on the guild?
            elif lexemes[item] == Lexeme.CHANNEL:
                if message.guild.get_channel(parsedInput[item]) != None:
                    parsedInput[item] = message.guild.get_channel(parsedInput[item])
                else:
                    await message.channel.send(
                        f"`Invalid channel: channel <#{parsedInput[item]}> does not exist on this server`")
                    return
            # parsedInput[item] = bot.get_channel(parsedInput[item])

        # RUN COMMAND
        # lexical and conversion succeeded: run command with good arguments
        await self.run(Context(message.author, message.channel, message), parsedInput[1:])


class Bot(discord.Client):
    def __init__(self):
        # Set intents
        intents = discord.Intents.all()
        intents.message_content = True
        super().__init__(intents=intents)

        # create dictionnary of name/commands defined here
        self.commands = {cmd.__name__.lower(): cmd() for cmd in
                         [cls_attribute for cls_attribute in self.__class__.__dict__.values() if
                          inspect.isclass(cls_attribute) and issubclass(cls_attribute, Command)]}
        # gives access to the bot to commands
        for command in self.commands.values(): command.bot = self
        self.settings = self.readJSONFrom('jsons/settings.json')

    async def on_ready(self):
        self.startTime = datetime.now()
        print(f'Bot connected as {self.user}.')
        print(f'Started at {self.startTime.strftime("%d/%m/%Y - %Hh%M")}.')
        print(f'List of commands: {self.commands.keys()}')

    # return Command class if the content of a message refers to an existing command AND the member has the authorization to call it, else return None
    def getCommand(self, message):
        first = message.content.split()[0]
        # does the command exists?
        if first[0] == Command.prefix and first[1:] in list(self.commands.keys()):
            # does the member has the minimum authorizationLevel to call it?
            if self.commands[first[1:]].authorizationLevel.value <= AuthorizationLevel.getMemberAuthorizationLevel(
                    message.author).value:
                return self.commands[first[1:]]
            else:
                return None
        else:
            return None

    def getDefaultEmbed(self, title, description, user, color=0xa748c3):
        embed = discord.Embed(title=title,
                              description=description,
                              colour=color,
                              timestamp=datetime.now())
        embed.set_author(name=user.display_name,
                         icon_url=user.avatar)
        embed.set_footer(text=f"Version {VERSION}",
                         icon_url="attachment://BotPFP.png")
        return embed

    def readJSONFrom(self, filepath):
        if not isfile(filepath): return json.loads("{}")
        return json.loads(open(filepath, 'r').read())

    def writeJSONTo(self, filepath, data):
        with open(filepath, 'w') as f:
            f.write(json.dumps(data))

    def updateSetting(self, set, value):
        def checkTypeCompatibility(type, value):
            match type:
                case "INT":
                    if isinstance(value, int): return value
                case "TEXT":
                    if isinstance(value, str): return value
                case "BOOL":
                    if isinstance(value, bool): return value
                case "USER":
                    if isinstance(value, discord.user.User): return value.id
                case "ROLE":
                    if isinstance(value, discord.role.Role): return value.id
                case "CHANNEL":
                    if isinstance(value, discord.channel.TextChannel): return value.id
            return None

        s = self.settings
        for k in set:
            if k not in s:
                return False
            s = s[k]
        # At end of loop, s is equal to setting to modify.
        if "type" not in s or "value" not in s: return False
        # If the update should be done manually with a different function...
        if "manualUpdate" in s: return self.manualUpdateSetting(s, value)

        type = s["type"]
        isArray = False
        # If JSON accepts null for this value...
        if type[0] == "!":
            type = type[1:]
            # If value is None, add it then return.
            if value is None:
                s["value"] = None
                self.writeJSONTo('jsons/settings.json', self.settings)
                self.settings = self.readJSONFrom('jsons/settings.json')
                return True

        # Checks if JSON accepts arrays.
        if type[0] == "[" and type[-1] == "]":
            type = type[1:-1]
            isArray = True

        # If it does...
        if isArray:
            # If value isn't an array, put it in an array with only itself as a value.
            if not isinstance(value, list):
                value = [value]

            rawValue = value
            value = []
            # Check that type of value corresponds for every item in array.
            for i in rawValue:
                if not checkTypeCompatibility(type, i):
                    return False  # Return if one of the value doesn't correspond to expected type
                value.append(checkTypeCompatibility(type, i))

        # Otherwise, check compatibility of the value.
        else:
            value = checkTypeCompatibility(type, value)
            if value is None:
                return False  # Return if type doesn't correpsond.

        s["value"] = value  # Finally, change value if everything corresponds.

        # Write it in the JSON...
        self.writeJSONTo('jsons/settings.json', self.settings)
        self.settings = self.readJSONFrom('jsons/settings.json')
        return True  # And return true

    def manualUpdateSetting(self, setting, value):
        # Used to update Twitch channels.
        if setting["manualUpdate"] == "TwitchChannel":
            token = self.getTwitchToken()
            response = requests.get(
                f"https://api.twitch.tv/helix/users?login={value.lower()}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "client-id": f"{self.settings['twitch']['OAuth']['id']['value']}"
                }
            )
            res = response.json()
            if "data" not in res or res["data"] == []:
                return False
            setting["value"] = int(res["data"][0]["id"])
            self.writeJSONTo('jsons/settings.json', self.settings)
            self.settings = self.readJSONFrom('jsons/settings.json')
            return True

    def getTwitchToken(self):
        token = self.readJSONFrom('jsons/twitchToken.json')
        if token:
            if token["expires_at"] > time.time():
                return token["access_token"]
        if self.settings['twitch']['OAuth']['id']['value'] is None or self.settings['twitch']['OAuth']['secret']['value'] is None:
            return None
        response = requests.post(
            "https://id.twitch.tv/oauth2/token",
            params={
                "client_id": self.settings['twitch']['OAuth']['id']['value'],
                "client_secret": self.settings['twitch']['OAuth']['secret']['value'],
                "grant_type": "client_credentials"
            }
        )
        token = response.json()
        token['expires_at'] = token['expires_in'] + time.time()
        self.writeJSONTo('jsons/twitchToken.json', token)
        return response.json()["access_token"]

    def getDateTime(self, hour, utc=False):
        format = "%Y-%m-%dT%H:%M:%SZ"
        timezone = tzlocal.get_localzone()
        day = datetime.strptime(hour, format).replace(tzinfo=pytz.utc)
        if not utc: return day.astimezone(timezone)
        return day

    def addModAction(self, mod, user, action, reason):
        if AuthorizationLevel.getMemberAuthorizationLevel(
                mod) != AuthorizationLevel.OWNER and AuthorizationLevel.getMemberAuthorizationLevel(
                mod).value <= AuthorizationLevel.getMemberAuthorizationLevel(user).value:
            return False
        with sqlite3.connect(f"{DB_FOLDER}{self.guild.id}") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO mod_log (mod, user, action, reason) VALUES (?, ?, ?, ?)",
                        (mod.id, user.id, action, reason))
        return cur.lastrowid




#####################
# DATABASE COMMANDS #
#####################
def getPrivileged(userID=None, presentOnly=False):
    guildId = json.loads(open('jsons/utils.json', 'r').read())['guildID']
    query = "SELECT * FROM privilege"
    if userID and not presentOnly: query += f" WHERE user = {userID}"
    if presentOnly and not userID: query += " WHERE startAt < CURRENT_TIMESTAMP AND endsAt > CURRENT_TIMESTAMP"
    if userID and presentOnly: query += f" WHERE startAt < CURRENT_TIMESTAMP AND endsAt > CURRENT_TIMESTAMP AND user = {userID}"

    with sqlite3.connect(f"{DB_FOLDER}{guildId}") as con:
        cur = con.cursor()
        res = cur.execute(query)
        res = res.fetchall()  # id, user, startsAt, endsAt
    if not res:
        return []
    else:
        privileged = []
    for i in res:
        line = {"id": i[0], "user": i[1],
                "startsAt": toDateTime(i[2], True), "endsAt": toDateTime(i[3], True)}
        privileged.append(line)
    return privileged


def toDateTime(field, timestamp=False):
    if field is None: return None

    # Everything is stored UTC time, need to get local timezone for correct time on Discord.
    localTimezone = tzlocal.get_localzone()
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S.%f+00:00"]
    for i in formats:
        try:
            time = datetime.strptime(field, i).replace(tzinfo=timezone.utc)
            if timestamp:
                return int(time.astimezone(localTimezone).timestamp())
            return time.astimezone(localTimezone)
        except ValueError:
            continue
    return None
