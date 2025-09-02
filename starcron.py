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


class Starcron(Bot):
    # Gets users that celebrate their birthday today
    def CheckBirthdays(self):
        def convertSQLiteTimeToDatetime(rawDate):
            return datetime.strptime(rawDate[0:10], '%Y-%m-%d')

        # checks for each person we know his/her birthday if it's today
        with sqlite3.connect(f"{DB_FOLDER}{self.guild.id}") as con:
            cur = con.cursor()
            res = cur.execute(
                f"SELECT * FROM birthday WHERE strftime('%m-%d', day) = strftime('%m-%d', 'now')")
            res = res.fetchall()

            print(res)

        if not res:
            return None

        msg = "🎂 "
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

        print("Done! Closing...")
        await self.close()

    async def runCronTasks(self):
        print("Running cron tasks...")

        # Task 1 - Check for potential birthdays
        print("Checking birthdays...")
        if self.settings['birthday']['enable']['value'] and self.settings['birthday']['channel']['value'] is not None:
            msg = self.CheckBirthdays()
            print(msg)
            if msg is not None:
                channel = self.guild.get_channel(self.settings['birthday']['channel']['value'])
                await channel.send(msg)

if __name__ == "__main__":
    sc = Starcron()
    sc.run(SHOOTINGSTAR_TOKEN, log_handler=logging.FileHandler(filename='starcron.log', encoding='utf-8', mode='w'), log_level=logging.DEBUG)