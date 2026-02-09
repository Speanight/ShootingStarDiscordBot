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
from Objects import Log, LogStatus


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
            if entry['age'] != 1900: msg += f", they're now {datetime.now().year - entry['age']} years old"
            msg += "! I've given you 5 mangoes to celebrate.\n"

            # Give mangoes for birthday
            self.updateMangoCount(i[0], count=self.settings['mango']['birthdayReward']['value'])

        return msg

    def addMangos(self, resetUsers=True, newDay=True):
        news = randint(1, self.settings['mango']['randomLimit']['value'])

        mangos = self.readJSONFrom(MANGO_FILE)

        if resetUsers: mangos['users'] = {}

        for mango in mangos['mangos']:
            if newDay: mango['delay'] = mango['delay'] + 1

            # Removes mangos that are standing still for 3 days:
            if mango['delay'] >= self.settings['mango']['mangoExpire']['value']:
                mangos['mangos'].remove(mango)

        for i in range(0, news):
            mangos['mangos'].append({"delay": 0})

        mangos['mangos'] = mangos['mangos'][:self.settings['mango']['limit']['value']]
        self.writeJSONTo(MANGO_FILE, mangos)

        return len(mangos['mangos'])

    async def on_ready(self):
        await super().on_ready()
        # connects botcron to guild
        self.guild = self.guilds[0]
        self.settings = self.readJSONFrom('jsons/settings.json')

        await self.runCronTasks()

        print("Done! Closing...")
        await self.close()

    async def runCronTasks(self):
        now = datetime.now()
        self.logs = self.readJSONFrom(CRON_LOGS)

        logs = {
            "tasks": [],
            "version": VERSION,
            "state": "pending"
        }

        # Check if cron has been run already (can be seen in logs)
        ranToday = now.strftime('%Y-%m-%d') in self.logs and len(self.logs[now.strftime('%Y-%m-%d')]) > 0

        print("Running cron tasks...")
        log = Log("Starting cron tasks", LogStatus.DEBUG)
        if ranToday:    log.message = "Cron-job already ran today: skipping some tasks"
        else:           log.message = "First cron-job of the day: running all tasks"
        logs['tasks'].append(log.toJSON())

        ### TASKS THAT EXECUTE ONLY ONCE ###
        if not ranToday:
            # Task 1 - Check for potential birthdays
            log = Log("Checking birthdays")
            if self.settings['birthday']['enable']['value'] and self.settings['birthday']['channel']['value'] is not None:
                try:
                    msg = self.CheckBirthdays()
                except Exception as e:
                    msg = None
                    log.status = LogStatus.ERROR
                    log.message = str(e)
                if log.status != LogStatus.ERROR:
                    if msg is not None:
                        channel = self.guild.get_channel(self.settings['birthday']['channel']['value'])
                        await channel.send(msg)
                        log.message = "Birthdays found and sent in channel"
                    else:
                        log.message = "No birthdays found!"
            else:
                log.status = LogStatus.INFO
                log.message = "Birthday feature disabled"

            log.end = datetime.now()
            logs['tasks'].append(log.toJSON())

        ### TASKS THAT EXECUTE ON EVERY ITERATION ###
        # Task 2 - Add mango to the basket
        log = Log("Adding mangoes")
        if self.settings['mango']['enable']['value']:
            log.message += f"Adding between 1 and {self.settings['mango']['randomLimit']['value']} mangos"
            msg = self.addMangos(not ranToday or self.settings['mango']['resetAtBatches']['value'], not ranToday)
            log.message += f" | User limits reset? {not ranToday or self.settings['mango']['resetAtBatches']['value']}"
            if self.settings['mango']['channel']['value'] is not None:
                channel = self.guild.get_channel(self.settings['mango']['channel']['value'])
                await channel.send(f"🔔 Mango batch deliveryy! <: 🥭 - There is now **{msg} mangos** available! Claim them with `!mango claim`")
            else:
                log.message = "No channel set to display mango batches"
                log.status = LogStatus.INFO
        else:
            log.status = LogStatus.INFO
            log.message = "Mango feature disabled"

        log.end = datetime.now()
        logs['tasks'].append(log.toJSON())

        # Write the logs in the log file:
        if not now.strftime('%Y-%m-%d') in self.logs:
            self.logs[now.strftime('%Y-%m-%d')] = {}
        logs['state'] = "completed"
        self.logs[now.strftime('%Y-%m-%d')][now.strftime('%H:%M')] = logs
        self.writeJSONTo(CRON_LOGS, self.logs)

if __name__ == "__main__":
    sc = Starcron()
    sc.run(getEnv('SHOOTINGSTAR_TOKEN'), log_handler=logging.FileHandler(filename='starcron.log', encoding='utf-8', mode='w'), log_level=logging.DEBUG)