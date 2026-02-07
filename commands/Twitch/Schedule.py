from botutils import *
from datetime import datetime, timedelta
import discord
import requests

class Schedule(Command):
    description = ("Gives the next planned streams of da purple pegasi! You can override default values and specify"
                   "amount of streams to display (1-25), or if you only want the streams of current week or not"
                   "(false/true)")
    authorizationLevel = AuthorizationLevel.MEMBER
    syntax = [[], [Lexeme.INT], [Lexeme.BOOL]]

    async def run(self, context, args):
        maxLimit = self.bot.settings['twitch']['schedule']['maxLimit']['value']
        perWeek = self.bot.settings['twitch']['schedule']['perWeek']['value']

        if maxLimit > 25: maxLimit = 25

        if len(args) == 1:
            # User specified to show per week.
            if isinstance(args[0], bool):
                perWeek = args[0]
                maxLimit = 25 # Maximum imposed by Twitch.

            # Specified amount of streams to show.
            elif isinstance(args[0], int):
                if 1 < args[0] < 25:
                    maxLimit = args[0]
                    perWeek = False # Disables per week view to display amount of stream requested (if applicable)


        token = self.bot.getTwitchToken()
        if token is None:
            await context.channel.send(f"❌ No twitch OAuth token is being used. Please set them in settings.")
        if self.bot.settings['twitch']['channel']['value'] is None:
            await context.channel.send(f"❌ No twitch channel is being monitored right now!")
            return
        response = requests.get(
            f"https://api.twitch.tv/helix/users?id={self.bot.settings['twitch']['channel']['value']}",
            headers={
                "Authorization": f"Bearer {token}",
                "client-id": f"{self.bot.settings['twitch']['OAuth']['id']['value']}"
            }
        )
        user = response.json()['data'][0]

        response = requests.get(
            f"https://api.twitch.tv/helix/schedule?broadcaster_id={self.bot.settings['twitch']['channel']['value']}&first={maxLimit}",
            headers = {
                "Client-ID": self.bot.settings['twitch']['OAuth']['id']['value'],
                "Authorization": f"Bearer {token}"
            }
        )
        schedule = response.json()['data']
        msg = ""

        if schedule['vacation'] is None or int \
                (self.bot.getDateTime(schedule['vacation']['end_time']).timestamp()) < int(datetime.now().timestamp()):
            for i in schedule['segments']:
                if not perWeek or int(self.bot.getDateTime(i['start_time']).timestamp()) < \
                        (datetime.now() + timedelta(days=(7 - datetime.now().weekday()))).replace(hour=0, minute=0,
                                                                                                 second=0,
                                                                                                 microsecond=0).timestamp():
                    msg += '- '
                    if i['is_recurring']: msg += '🔁'
                    msg += f"<t:{int(self.bot.getDateTime(i['start_time']).timestamp())}:f> | **{i['category']['name']}**: {i['title']}\n"
        else:
            msg = f"{user['display_name']} is in **Vacation** right now!\nThey will return with awesome content starting <t:{int(self.bot.getDateTime(schedule['vacation']['end_time']).timestamp())}:F>!"

        author = "Twitch Schedule - "
        if perWeek:
            author += "Week schedule"
        else:
            author += f"{maxLimit} next streams"

        # And add everything to an embed.
        embed = discord.Embed(title=user['display_name'],
                              url=f"https://twitch.tv/{user['login']}",
                              description=msg,
                              colour=0xa748c3,
                              timestamp=datetime.now())
        embed.set_author(name=author)
        embed.set_thumbnail(url=user['profile_image_url'])
        embed.set_footer(text=f"Version {VERSION}", icon_url="attachment://BotPFP.png")
        if schedule['vacation'] is not None: embed.set_image(url=user['offline_image_url'])

        await context.channel.send(embed=embed)