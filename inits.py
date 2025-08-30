import sqlite3
import json
from botutils import ModActions, DB_FOLDER
from os.path import isfile


def initDB(name):
    with sqlite3.connect(f"{DB_FOLDER}{name}") as con:
        cur = con.cursor()

        cur.execute("""CREATE TABLE IF NOT EXISTS action_type (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE)
                    """)

        cur.execute("""CREATE TABLE IF NOT EXISTS mod_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        mod INTEGER NOT NULL,
                        user INTEGER,
                        action INTEGER NOT NULL,
                        reason TEXT,
                        timestamp DATETIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        pardon INTEGER DEFAULT 0,
                        pardonTimestamp DATETIME TIMESTAMP DEFAULT NULL,
                        pardonReason TEXT DEFAULT NULL,
                        FOREIGN KEY (action) REFERENCES action_type(id)
                        )""")

        cur.execute("""CREATE TABLE IF NOT EXISTS birthday (
                        user INTEGER PRIMARY KEY,
                        day DATE NOT NULL)""")

        cur.execute("""CREATE TABLE IF NOT EXISTS privilege (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user INTEGER NOT NULL,
                        startAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                        endsAt DATETIME NOT NULL)
                        """)

        cur.execute("""CREATE TABLE IF NOT EXISTS birthday (
                        user INTEGER PRIMARY KEY,
                        bday DATE NOT NULL)""")

        actions = [i for i in ModActions]

        for i, action in enumerate(actions, start=1):
            cur.execute("""
            INSERT OR IGNORE INTO action_type (id, name)
            VALUES (?, ?)
            """, (i, str(action)))
        con.commit()

def initSettings():
    # Checks that default settings exists.
    if not isfile('jsons/defaultSettings.json'):
        print("defaultSettings.json file doesn't exist!")
        return -1
    defaultSettings = json.loads(open('jsons/defaultSettings.json', 'r').read())

    # If settings file doesn't exist, then just copy default ones.
    if not isfile('jsons/settings.json'):
        print("Settings doesn't exist: dumping default settings!")
        with open('jsons/settings.json', 'w') as f:
            f.write(json.dumps(defaultSettings))
        return

    settings = json.loads(open('jsons/settings.json', 'r').read())

    # Manages missing keys for settings. (recursive, hence the def)
    def merge_defaults(default, current):
        # checks each key in default.
        for key, value in default.items():
            # If the key doesn't exist, add it with default values.
            if key not in current:
                print(f"Adding {key} to settings!")
                current[key] = value
            # Otherwise, if key exists but is a dict, recursive into it.
            elif isinstance(value, dict) and isinstance(current.get(key), dict):
                merge_defaults(value, current[key])
        return current

    # Merges the values between the default and the settings.
    newSettings = merge_defaults(defaultSettings, settings)

    with open('jsons/settings.json', 'w') as f:
        f.write(json.dumps(newSettings))