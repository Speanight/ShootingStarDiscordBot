# MIT Licence
# authors: Luna and Yashn

import discord
import logging
from datetime import datetime

from tokens import SHOOTINGSTAR_TOKEN
from botutils import Bot, Command, DB_FOLDER
import requests
from datetime import datetime, timedelta, date
import tzlocal
import pytz
import sqlite3

BIRTHDAYS_FILE = "jsons/birthdays.json"


class Starcron(Bot):
    # Gets users that celebrate their birthday today
    def CheckBirthdays(self):
        def convertSQLiteTimeToDatetime(rawDate):
            return datetime.strptime(rawDate[0:10], '%Y-%m-%d')

        # checks for each person we know his/her birthday if it's today
        with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
            cur = con.cursor()
            res = cur.execute(
                f"SELECT * FROM birthday WHERE bday >= date('now', 'start of day')")
            res = res.fetchall()

        msg = ""

        if res == []:
            return None

        for i in res:
            date = convertSQLiteTimeToDatetime(i[1])
            entry = {"user": f"<@{i[0]}>", "age": date.year}

            msg += f"Happy birthday to {entry['user']}"
            # 1900 is default value for date, checking if age was given by person...
            if entry['age'] != 1900: msg += f", they're now {entry['age']} years old"
            msg += "!\n"

        return msg

    async def on_ready(self):
        await super().on_ready()
        # connects botcron to guild
        self.guild = self.guilds[0]
        print(f'Cron connected on server: {self.guild.name}.')
        self.settings = self.readJSONFrom('jsons/settings.json')

        await self.runCronTasks()

        print("Done!")
        # await self.close()

    async def runCronTasks(self):
        print("Running cron tasks...")
        # Task 1 - Check for potential birthdays
        if self.settings['birthday']['enable'] and self.settings['birthday']['channel'] is not None:
            msg = self.CheckBirthdays()
            if msg is not None:
                await self.settings['birthday']['channel'].send(msg)

if __name__ == "__main__":
    sc = Starcron()
    sc.run(SHOOTINGSTAR_TOKEN, log_handler=logging.FileHandler(filename='starcron.log', encoding='utf-8', mode='w'), log_level=logging.DEBUG)