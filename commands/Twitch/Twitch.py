from botutils import Command, AuthorizationLevel, VERSION
from datetime import datetime
import requests
import discord

class Twitch(Command):
    description = "Outputs the current Twitch channel checked by the bot"
    authorizationLevel = AuthorizationLevel.MEMBER
    syntax = [[]]

    async def run(self, context, args):
        # Recovers Twitch channel ID
        id = self.bot.settings['twitch']['channel']['value']
        if id is None:
            # If Twich channel not setup...
            await context.channel.send(f"❗ No twitch channel is being monitored right now!")
            return
        token = self.bot.getTwitchToken()

        # Otherwise, get all details about twitch channel.
        response = requests.get(
            f"https://api.twitch.tv/helix/users?id={id}",
            headers={
                "Authorization": f"Bearer {token}",
                "client-id": f"{self.bot.settings['twitch']['OAuth']['id']['value']}"
            }
        )
        res = response.json()['data'][0]

        # And add everything to an embed.
        embed = discord.Embed(title=res['display_name'],
                              url=f"https://twitch.tv/{res['login']}",
                              description=f"> {res['description']}\n\n**Status:** {res['broadcaster_type']}",
                              colour=0xa748c3,
                              timestamp=datetime.now())
        embed.set_author(name="Twitch Channel")
        embed.set_image(url=res['offline_image_url'])
        embed.set_thumbnail(url=res['profile_image_url'])
        embed.set_footer(text=f"Version {VERSION}", icon_url="attachment://BotPFP.png")

        await context.channel.send(embed=embed)