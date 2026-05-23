from Objects.ShopItem import ShopItem
from botutils import *

SHOP_ITEMS = "jsons/shop/shop.json"
SHOP_PURCHASES = "jsons/shop/purchases.json"

class Shop(Command):
    description = ("You've worked hard enough to get some mangoes? Or perhaps you gambled them away and was lucky enough "
                   "to gamble them away and get more than what you initially had, and now you want to spend them?\n"
                   "Well, the shop is here exactly for this reason!")
    authorizationLevel = AuthorizationLevel.MEMBER
    syntax = [[], [Lexeme.INT]]

    async def claimReward(self, item, user):
        match item.reward:
            case "role":
                forbiddenRoles = [self.bot.settings['moderation']['admin']['value'],
                    self.bot.settings['moderation']['staff']['value'],
                    self.bot.settings['moderation']['trialstaff']['value'],
                    self.bot.settings['moderation']['member']['value']]

                if item.rewardValue not in forbiddenRoles:
                    role = self.bot.guild.get_role(item.rewardValue)
                    await user.add_roles(role, reason="mango shop")
                    return
                else:
                    print(f"I can't give such a sensitive role to an user!")
        await asyncio.sleep(0)


    async def run(self, context, args):
        # Gets all items in the shop:
        shop = {}
        items = self.bot.readJSONFrom(SHOP_ITEMS)
        for item in items:
            shop[items[item]["id"]] = ShopItem(items[item])
        # Get a list of what user already unlocked:
        purchases = self.bot.readJSONFrom(SHOP_PURCHASES)


        # If user wants to display shop:
        if len(args) == 0:
            description = f"There are **{len(shop)}** items in shop:\n"

            toBuy, alreadyBought = "", ""

            for id, item in shop.items():
                temp = f"- {item.emoji} **{item.name} [ID: {item.id}]:** {item.price}  🥭\n"
                if str(context.author.id) in purchases and id in purchases[str(context.author.id)]:
                    alreadyBought += temp
                else:
                    toBuy += temp

            description += "```Items to buy```\n" + toBuy + "```Items already bought```\n" + alreadyBought


            embed = self.bot.getDefaultEmbed("Shop", description, context.author)

            await context.channel.send(embed=embed)
            return


        # If user wants to buy something from the shop:
        if len(args) == 1:
            item = args[0]

            if item not in shop:
                message = "❌ This item doesn't exist in the shop!"

            elif str(context.author.id) in purchases and item in purchases[str(context.author.id)]:
                message = "❗ You already bought this item!"

            else:
                # Get and remove the corresponding amount of mangoes if possible:
                mangoes = self.bot.getMangoBalance(context.author.id)
                if mangoes >= shop[item].price:
                    with sqlite3.connect(f"{DB_FOLDER}{self.bot.guild.id}") as con:
                        cur = con.cursor()
                        cur.execute(f"UPDATE mango SET mango = ? WHERE user = ?", (mangoes-shop[item].price, context.author.id))
                    message = f"✅ You successfully bought {shop[item].name}!"
                    # Add item to list of items bought:
                    if str(context.author.id) not in purchases:
                        purchases[str(context.author.id)] = []
                    purchases[str(context.author.id)].append(shop[item].id)
                    self.bot.writeJSONTo(SHOP_PURCHASES, purchases)

                    # Add reward if exists:
                    await self.claimReward(shop[item], context.author)


                else:
                    message = "❗ You don't have enough mangoes to buy this item!"

            await context.channel.send(message)