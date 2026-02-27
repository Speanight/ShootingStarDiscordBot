from botutils import *
import subprocess
import os.path


class Update(Command):
    description = ("Allows you to update the bot or check the version installed:\n"
                   "!update (check) | Allows you to check the latest version and compare it."
                   "!update info | Allows you to get the current version details."
                   "!update run | Allows you to run the update of the bot.")
    authorizationLevel = AuthorizationLevel.PRIVILEGED
    syntax = []

    async def run(self, context, args):
        action = args

        if action: action = action[0]

        if not os.path.exists("./update.sh"):
            await context.channel.send("❌ - ERROR: The script couldn't be found!")
            return

        msg = "I did not understand that! Args can be empty, 'check', 'info' or 'run'."

        if not action or action == "check":
            version = subprocess.check_output(['sh', "./update.sh", "-c"], text=True).strip()

            if version == "0":
                msg = "✅ - The bot is up to date!"
            else:
                msg = f"❓ The bot can be updated to version {version}. You can update it now by running !update run"

        elif action == "info":
            version = subprocess.check_output(['sh', "./update.sh", "-i"], text=True).strip()

            msg = f"ℹ️ - The bot is on version {version}"

        elif action == "run":
            await context.channel.send("I will try to run the update. The bot will appear as offline during that time!")

            subprocess.check_output(['sh', "./update.sh", "-u"])

            return

        await context.channel.send(msg)
