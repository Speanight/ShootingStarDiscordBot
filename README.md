# ShootingStar Bot - Discord

Welcome to my Discord bot Repo!

Shooting Star is an open-source discord bot running through discord. It has been thought to try and become a general-purpose bot, offering functions such as:
- **Role management** (autorole, reactions-role, ...)
- **Administrative actions** (mute, lockdown, kick, ban, as well as a detailed mod logs kept in a SQLite DB)
- **Twitch integrity** (bot status according to planning, commands to get schedule, auto-announcements, ...)

If you're looking for one bot that would do all of this (and more to come!) instead of adding hundreds of bot to your server, this is it!

## Install
> [!IMPORTANT]
> Those steps are mandatory for the bot. If you do not follow them, the bot might crash on some steps, or not run at all!
> 
> Please make sure to follow those steps in order:

1. Install a recent version of Python (preferably Python3) - venv work too!
2. Install pip if needed: py -m pip install --upgrade pip
3. pip install -U discord.js
4. You might need to install the following pip packages:
   1. discord.js
   2. pytz
   3. tzlocal
   4. datetime
   5. python-dotenv
5. You need to create a file in images/ called BotPFP.png. This will be used in embed.
6. You also need to create a `.env` file with the following content:
```
SHOOTINGSTAR_TOKEN=Insert here your Discord Bot Token
TWITCH_ID=Insert here your twitch id
TWITCH_TOKEN=Insert here your twitch token
```
> [!NOTE]
> [Here](https://discordpy.readthedocs.io/en/stable/discord.html) you can find the steps to create your discord bot and get the token (that you should put in "SHOOTINGSTAR_TOKEN").

7. Once you get the bot running, you might want to run the command `!settings` in a private channel. You can get help on a command by typing `!settings help <command>`, and you can change the settings value by typing `!settings update <setting> <value>`.

> [!NOTE]
> To get the bot to work with its Twitch API, you will need to set the OAuth ID and key through the settings command.
> [Here](https://dev.twitch.tv/docs/authentication/register-app/) you can find the required steps to create your Twitch app, and get your OAuth ID and Secret.

> [!CAUTION]
> Even if the twitch OAuth ID is considered as an info that can be considered public, your secret should always be kept private. You can edit manually the `jsons/settings.json` file, or you can go through discord commands, but it is recommended to share the twitch secret only in a private channel.
> Keep in mind that a OAuth token is similar to a password: anyone that has it can act as your app and run whatever code they want. Same goes with your Discord token.

You can also create a service for the bot itself, by adding a new file inside `/etc/systemd/system/file.service`:
```ini
[Unit]
Description=Discord Bot (Shooting Star) service
After=network.target

[Service]
Type=simple
Restart=always
RestartSec=1
User=ShootingStar
WorkingDirectory=/var/discordBot
ExecStart=/srv/python/venv/bin/python3 /var/discordBot/ShootingStar.py

[Install]
WantedBy=multi-user.target
```

## Updates
**Version 1.0.0:** First release of the bot. So far, the bot is able to do basic moderation actions, as well as twitch actions and plan messages.

## Upcoming changes
> [!NOTE]
> The changes noted here are potential improvements for the bot, taken from my personal use as well as potential suggestions. None of what is written down there is actually planned, but more of a general idea of the direction that I will be taking with this bot development.

- **Needs to be fixed**
  - Privileged access through SQLite
  - Some commands might not work and still have their description in French due to adaptation of bot.
- **Being Worked on**
  - Auto announcement of Twitch schedule
- **Being considered**
  - More member commands (8ball, custom commands, random % generator, ...)

## Thanks, licenses and more
Everyone is free to use the bot and fork it as long as mentions are added (minimum repo, embed footer in discord or a command for sources would be greatly appreciated!)

Feel free to copy/paste the following text if needed:

```
Shooting Star bot - https://github.com/Speanight
Created by Furball
Base of the bot made by Yashn37 and Furball.
```