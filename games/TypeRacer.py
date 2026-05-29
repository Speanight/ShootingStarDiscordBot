import discord

from games.Game import *
from games.gameutils import TYPERACER_QUOTES
import random
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap

class TypeRacer(Game):
    def __init__(self):
        super().__init__("Typeracer", GameType.TYPERACER.value, 2, 25)
        self.rules = (f"In Typeracer, the bot will send a random sentence, and people will have to type "
                      f"it out as quickly as possible. The one that sends the EXACT sentence (punctuation"
                      f" and caps included!) will win the minigame!")

    async def start(self, session):
        result = await super().start(session)
        if not result: return result

        # Game:
        text = random.choice(TYPERACER_QUOTES)
        session.values["text"] = text # Keeps track of the text in the session.

        # Generate image:
        img = Image.new("RGB", (640, 360), color="white")
        draw = ImageDraw.Draw(img)

        font = ImageFont.load_default(size=40)

        margin = offset = 25
        for line in textwrap.wrap(text, width=25):
            draw.text((margin, offset), line, font=font, fill="black")
            offset += font.getbbox(line)[3]

        # Keep the image in memory:
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        await session.thread.send(file=discord.File(buffer, "TypeRacer.png"))

        buffer.close()

        return True

    async def handleMessage(self, session, message: discord.Message):
        if message.content == session.values["text"]:
            return await self.handleWinner(session, message.author)
        else: return False