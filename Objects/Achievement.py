from datetime import datetime
from enum import Enum
from botutils import VERSION

import discord


class RewardType(Enum):
    ROLE = 1
    MANGO = 2


class Achievement:
    def __init__(self, id=-1, title="", description="", emoji=None, condition="", secret=False, rewards=None, rewardTypes=None):
        self.id = id

        self.title = title
        self.description = description
        self.emoji = emoji
        self.condition = condition
        self.secret = secret

        self.rewards = rewards # [] otherwise
        self.rewardTypes = rewardTypes # [] otherwise

    def toTuple(self):
        return self.title, self.description, self.emoji, self.condition, self.secret

    def toTupleRewards(self):
        ret = []
        for i in range(self.rewards):
            ret.append((self.rewards[i], self.rewardTypes[i]))
        return ret

    def toEmbed(self):
        embed = discord.Embed(
            title = f"{self.emoji} ACHIEVEMENT #{self.id} - {self.title}",
            description = self.description,
            colour = 0xffff82,
            timestamp = datetime.now()
        )
        embed.set_footer(text=f"Version {VERSION}", icon_url="attachment://BotPFP.png")

        if self.secret:
            embed.description = f"🔒 This achievement is secret! Therefor, you cannot get details about said achievement!"

        return embed