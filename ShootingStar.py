# MIT Licence
# authors: Luna

import logging
import random
from datetime import timedelta
from inits import *
from discord.ext import tasks
from discord.utils import get
import os

from botutils import *


class ShootingStar(Bot):
    # Checks if a message needs to be sent in a channel.
    @tasks.loop(minutes=1)
    async def messagePlanner(self):
        msg = self.readJSONFrom('jsons/plannedMessages.json')
        newMsg = []
        now = datetime.now().timestamp()
        for i in msg:
            if now > i['time']:
                try:
                    channel = self.get_channel(i['channel'])
                    if len(i['embed']) > 0:
                        file = discord.File(f"files/{i['embed'][0]}")
                        await channel.send(i['msg'], file=file)
                        os.remove(f"files/{i['embed'][0]}")
                    else:
                        await self.sendMessage(channel, i['msg'], i['author'])
                except Exception as e:
                    print(f"Failed to send message {i['id']}! Error: {e}")
                    newMsg.append(i)
            else:
                newMsg.append(i)

        if not newMsg:
            print(f"Stopping messagePlanner execution...")
            self.messagePlanner.stop()
        self.writeJSONTo('jsons/plannedMessages.json', newMsg)

    @tasks.loop(minutes=1)
    async def modActionPardon(self):
        actions = self.readJSONFrom('jsons/modactions.json')
        newActions = []
        now = datetime.now().timestamp()
        if not actions:
            print(f"Stopping modActionPardon execution...")
            self.modActionPardon.stop()
        for i in actions:
            if now > i['pardon']:
                if i['action'] == ModActions.MUTE.value:
                    user = self.guild.get_member(i['user'])
                    await user.remove_roles(get(self.guild.roles, id=self.settings['moderation']['muted']['value']))

                if i['action'] == ModActions.BAN.value:
                    user = await self.fetch_user(i['user'])
                    await self.guild.unban(user)

            else:
                newActions.append(i)

        self.writeJSONTo('jsons/modactions.json', newActions)


    # TODO: https://discordpy.readthedocs.io/en/stable/api.html?highlight=reaction#discord.on_reaction_add
    # Checks twitch status.
    @tasks.loop(minutes=10)
    async def twitchStatus(self):
        updateStatus = self.settings['twitch']['schedule']['automaticStatus']['value']
        id = self.settings['twitch']['channel']['value']

        if updateStatus and id is not None:
            print("Updating status...")
            TWITCH_ID = getEnv('TWITCH_ID')
            # Recovering data with Twitch API
            token = self.getTwitchToken()
            response = requests.get(
                f"https://api.twitch.tv/helix/schedule?broadcaster_id={self.settings['twitch']['channel']['value']}&first=1",
                headers={
                    "Client-ID": TWITCH_ID,
                    "Authorization": f"Bearer {token}"
                }
            )
            schedule = response.json()['data']

            response = requests.get(
                f"https://api.twitch.tv/helix/streams?user_id={self.settings['twitch']['channel']['value']}",
                headers={
                    "Client-ID": TWITCH_ID,
                    "Authorization": f"Bearer {token}"
                }
            )
            stream = response.json()['data']

            print("Twitch API done!")
            print(f"Stream: {stream}")
            print(f"Schedule: {schedule}")

            # If streamer is on vacation:
            if schedule['vacation'] is not None and ('end_time' in schedule['vacation'] and int(
                    self.getDateTime(schedule['vacation']['end_time']).timestamp()) > int(datetime.now().timestamp())):
                status = discord.Status.dnd
                activity = discord.CustomActivity(
                    name=f"In vacation! Back the {self.getDateTime(schedule['vacation']['end_time']).strftime('%d %B')}",
                    emoji="☀️")
                self.twitchStatus.change_interval(hours=24)

            # Otherwise, if live right now:
            elif stream:
                stream = stream[0]
                status = discord.Status.online
                activity = discord.Streaming(platform="Twitch", url=f"https://twitch.tv/{stream['user_login']}",
                                           twitch_name=stream['user_login'], name=stream['title'], game=stream['game_name'])
                self.twitchStatus.change_interval(minutes=5)

            # Otherwise: if a stream is planned:
            elif schedule['segments']:
                status = discord.Status.online
                activity = discord.CustomActivity(
                    name=f"Next stream planned {self.getDateTime(schedule['segments'][0]['start_time'], True).strftime('%d/%m %H:%M')} UTC")
                self.twitchStatus.change_interval(hours=1)

            # Otherwise: if no stream is planned:
            else:
                print("No stream planned...")
                status = discord.Status.idle
                activity = discord.CustomActivity(name=f"No stream planned! (yet!)", emoji="⏰")
                self.twitchStatus.change_interval(hours=12)

            print(f"Updating status...")

            await self.change_presence(status=status, activity=activity)

    #######################
    # ON MESSAGE RECEIVED #
    #######################

    async def on_message(self, message):
        await self.wait_until_ready()
        # Snow Pearl doesn't answer to its own messages or empty messages
        if message.author == self.user or message.content == "": return

        # is message trying to call an existing command?
        cmd = self.getCommand(message)
        if cmd is not None:
            await cmd.ParseAndTrySafeRun(self, message)

        # For custom reactions to messages, add else: condition and check message content.

    ####################
    # EVENT FUNCTIONS  #
    ####################

    async def on_ready(self):
        await super().on_ready()
        self.guild = self.guilds[0]
        print(f'Server: {self.guild.name}.')
        print(f"Creating DB...")
        initDB(self.guild.id)
        print("Checking settings...")
        initSettings()
        self.settings = self.readJSONFrom('jsons/settings.json')
        print("Checking if owner is in settings...")
        if self.settings['moderation']['owner']['value'] is None:
            print("It is: replacing None to owner ID...")
            self.settings['moderation']['owner']['value'] = self.guild.owner.id
            self.writeJSONTo('jsons/settings.json', self.settings)
        print(f"Writing guild ID in utils.json...")
        utils = self.readJSONFrom('jsons/utils.json')
        utils['guildID'] = self.guild.id
        self.writeJSONTo('jsons/utils.json', utils)
        self.silent_logs = self.settings['logs']['channel']['value']

        print(f'Starting repeated tasks...')
        self.messagePlanner.start()
        self.modActionPardon.start()
        print(f'Ready!')

        self.twitchStatus.start()

    async def on_member_join(self, member):
        # Add the roles in the list.
        if self.settings['newcomers']['roles']['value'] is not []:
            for role in self.settings['newcomers']['roles']['value']:
                try:
                    await member.add_roles(discord.utils.get(member.guild.roles, id=role))
                except discord.Forbidden:
                    pass

        # Add the member role if server isn't in Lockdown.
        if self.settings['moderation']['member']['value'] is not None and self.settings['moderation']['lockdownMode']['value'] is False:
            try:
                await member.add_roles(discord.utils.get(member.guild.roles, id=self.settings['moderation']['member']['value']))
            except discord.Forbidden:
                pass

        # Adds the log if settings says to:
        if self.settings['logs']['channel']['value'] is not None and self.settings['logs']['memberJoin']['value'] is True:
            embed = self.bot.getDefaultEmbed("User joined", f"User **{member.name}** joined the server.\nAccount created the: {member.created_at.day}/{member.created_at.month}/{member.created_at.year}", member, discord.Colour.green())
            await self.settings['logs']['channel']['value'].send(embed=embed)

    async def on_member_remove(self, member):
        # Adds the log if settings says to:
        if self.settings['logs']['channel']['value'] is not None and self.settings['logs']['memberLeave']['value'] is True:
            embed = self.bot.getDefaultEmbed("User left", f"User **{member.name}** left the server.", member, discord.Colour.red())
            await self.settings['logs']['channel']['value'].send(embed=embed)

    async def on_member_update(self, member_old, member_new):
        if member_old.display_name != member_new.display_name:
            embed = discord.Embed(title="User updated", color=discord.Colour.gold(),
                                  description=f"User **{member_new.name}** changed their username.\nChange: {member_old.display_name} -> {member_new.display_name}")
            embed.set_thumbnail(url="attachment://icon_update.png")
            embed.set_footer(text=f"User ID: {member_new.id}")

            # Adds the log if settings says to:
            if self.settings['logs']['channel']['value'] is not None and self.settings['logs']['memberUpdate'][
                'value'] is True:
                embed = self.bot.getDefaultEmbed("User updated",
                                                 f"User changed their display name: **{member_old.name} -> {member_new.name}**",
                                                 member_new, discord.Colour.gold())
                await self.settings['logs']['channel']['value'].send(embed=embed)

    ####################
    # USEFUL FUNCTIONS #
    ####################
    # send a list of string in channel as separate messages. Messages starting with ./images/ are treated like files
    async def send_all(self, channel, texts):
        for text in texts:
            if text.startswith("./images/"):
                try:
                    with open(text, 'rb') as file:
                        await channel.send(file=discord.File(file))
                except FileNotFoundError:
                    continue
            else:
                await channel.send(text)

    # returns true iif all elements in l are in content
    def all_in(self, content, l):
        return all([True if element in content else False for element in l])

    # returns true if any element in l is in content
    def any_in(self, content, l):
        return any([True if element in content else False for element in l])


if __name__ == "__main__":
    star = ShootingStar()

    star.run(getEnv('SHOOTINGSTAR_TOKEN'), log_handler=logging.FileHandler(filename='shootingstar.log', encoding='utf-8',
                                                                 mode='w')) #, log_level=logging.DEBUG)
