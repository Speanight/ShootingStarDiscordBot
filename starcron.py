from random import randint

import discord
import logging
from datetime import datetime

from botutils import *
import requests
from datetime import datetime, timedelta, date
import tzlocal
import pytz
import sqlite3
from random import randint


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

    def addMangos(self):
        print(f'Adding mangos to {self.guild.id}')

        news = randint(1, 5)
        amt = news

        mangos = self.readJSONFrom(MANGO_FILE)

        mangos['users'] = []

        for mango in mangos['mangos']:
            mango['delay'] = mango['delay'] + 1

            # Removes mangos that are standing still for 3 days:
            if mango['delay'] == 3:
                mangos.remove(mango)
            else:
                amt += mango['amount']

        # TODO: write architecture somewhere!
        mangos['mangos'].append(newMango)
        for i in range(0, news):
            mangos['mangos'].append()
        self.writeJSONTo(MANGO_FILE, mangos)

        return amt

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

        # Task 2 - Add mango to the basket
        print("Adding mangos...")
        if self.settings['mango']['enable']['value']:
            msg = self.addMangos()
            if self.settings['mango']['channel']['value'] is not None:
                channel = self.settings['mango']['channel']['value']
                await channel.send(f"🥭 - There is now {msg} mangos available! Claim them with !mango claim <amount>")

if __name__ == "__main__":
    sc = Starcron()
    sc.run(getEnv('SHOOTINGSTAR_TOKEN'), log_handler=logging.FileHandler(filename='starcron.log', encoding='utf-8', mode='w'), log_level=logging.DEBUG)