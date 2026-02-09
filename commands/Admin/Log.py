from botutils import *
from Objects import LogStatus

class Log(Command):
    description = ("Outputs logs data. Use no argument to see all available logs.\n"
                   "First argument is the log file to check (ie: 'cron' will check for cron logs).\n"
                   "Second argument is the verbosity (1 = Everything, 2 = Info, 3 = Warn, 4 = Errors.\n"
                   "Third argument is the name of the array (aka the date, often). ie: 2020-01-01.")
    authorizationLevel = AuthorizationLevel.STAFF
    syntax = [[], [Lexeme.TEXT], [Lexeme.TEXT, Lexeme.INT], [Lexeme.TEXT, Lexeme.INT, Lexeme.TEXT]]

    async def run(self, context, args):
        file, verbose, date = (args + [None] * 3)[:3]

        def readLogs(path, verbose, date):
            logs = self.bot.readJSONFrom(path)
            msg = ""

            if date is None:
                msg = "# Available logs\n"
                for day, data in logs.items():
                    msg += f"- **{day}** - *[{len(data)} items]*\n"
                    for time, _ in data.items():
                        msg += f"  - {time}\n"
            else:
                if date in logs:
                    msg = f"# Logs from {date}\n"
                    for time, data in logs[date].items():
                        msg += f"## {time}\n"
                        for task in data['tasks']:
                            if verbose <= LogStatus[task['status']].value:
                                msg += f"- {LogStatus[task['status']].toEmoji()} "
                                msg += f"**{task['task']}:** {task['message']}\n"
                        msg += f"> **Bot's version:** {data['version']}\n"
                        msg += f"> **State:** {data['state']}\n"

                else:
                    msg = f"Date {date} not found in logs!"

            return msg

        if not file or file == "cron":
            msg = readLogs(CRON_LOGS, verbose, date)

        else:
            msg = "❌ No log file found!"

        await context.channel.send(embed=self.bot.getDefaultEmbed(title="", description=msg, user=context.author))