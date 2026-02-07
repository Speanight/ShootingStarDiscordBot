from botutils import *

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
            if action not in COMMAND_HELP and len(args) < 3:
                value = None
            elif action not in COMMAND_HELP:
                value = args[2]

            if action in COMMAND_HELP:
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