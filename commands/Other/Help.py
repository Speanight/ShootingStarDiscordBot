from botutils import *

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
            for i in range(len(commandsByAuthorization)-1):
                msg += f"```{authorizations[i]}```\n {commandsByAuthorization[i][:-2]}\n"
        else:
            if args[0].lower() in dict(self.bot.allCommands.items()):
                command = dict(self.bot.allCommands.items())[args[0].lower()]
                desc = getattr(command, 'description').replace('\n', '\n> ')
                msg = f"> **{self.prefix}{args[0]}** - {desc}\n\n"
                if (AuthorizationLevel.getMemberAuthorizationLevel(
                        context.author).value >= AuthorizationLevel.STAFF.value):
                    msg += f"__**Authorization needed:**__ {getattr(command, 'authorizationLevel')}\n"
                if command.getCorrectSyntax():
                    syntaxes = '\n'.join(
                        f"- {self.prefix}{args[0]} {syntax}".strip() for syntax in command.getCorrectSyntax())
                    msg += f"\n**Syntaxes:**\n{syntaxes}\n\n"

                if command.aliases:
                    msg += f"**Aliases:**\n"
                    msg += '\n'.join(f"- !{aliases}" for aliases in command.aliases)
            else:
                await context.channel.send(
                    f"❌ <@{context.author.id}>, I do not recognize `{args[0]}` as one of my commands!")
                return

        embed = self.bot.getDefaultEmbed(f"Help - {args[0]}", msg, context.author)
        await context.channel.send(embed=embed)