import json

class ShopItem:
    def __init__(self, jsonArr):
        self.id = jsonArr["id"]
        self.emoji = jsonArr["emoji"]
        self.name = jsonArr["name"]
        self.price = jsonArr["price"]
        self.reward = jsonArr["reward"]
        self.rewardValue = jsonArr["rewardValue"]

    def toJson(self):
        return json.dumps(self.__dict__)
