import util
import json
import urllib.parse
import urllib.request
import calendar
import logging
from hook import Hook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = None
config = None
gift_string = None


def on_init(discord_client, module_config):
    global client, config, gift_string
    client = discord_client
    config = module_config
    update_gift_string()

    Hook.get("on_reset").attach(update_gift_string)
    Hook.get("public!gift").attach(gift_message)


async def gift_message(message, args):
    """
    Provides details about the dragons who receive and extra bonus from today's gift in the Dragon Roost.
    """
    await client.send_message(message.channel, gift_string)


def update_gift_string():
    global gift_string

    reset_day = util.get_reset_day()

    if reset_day >= 5:
        gift_target = "your favourite dragon!"
    else:
        logger.info("Requesting today's preferred dragons")
        request = "https://dragalialost.gamepedia.com/api.php?action=cargoquery&tables=Dragons&format=json&limit=500" \
                  "&fields=FullName,Rarity,ElementalTypeId" \
                  "&order_by=Rarity+DESC,+ElementalTypeId+ASC,+Id+DESC,+FullName+ASC" \
                  "&where=FavoriteType%3D" + str(reset_day + 1)

        with urllib.request.urlopen(request) as response:
            dragon_info_list = json.loads(response.read().decode())["cargoquery"]
            elemental_types = ["fire", "water", "wind", "light", "dark"]

            dragon_info = map(lambda d: {
                "name": d["title"]["FullName"],
                "emote": util.get_emote(config, elemental_types[int(d["title"]["ElementalTypeId"])-1]),
                "rarity": d["title"]["Rarity"]
            }, dragon_info_list)

            current_rarity = 6
            gift_target = "one of these dragons:"
            for dragon in dragon_info:
                gift_target += "\n"
                if int(dragon["rarity"]) < current_rarity:
                    current_rarity = int(dragon["rarity"])
                    gift_target += "\n" + current_rarity * util.get_emote(config, "rarity"+str(current_rarity)) + "\n"

                gift_target += dragon["emote"] + " " + dragon["name"]

    gift_string = "It's " + calendar.day_name[reset_day] + ", so give your best gift to " + gift_target

    logger.info("Completed requesting today's preferred dragons")


Hook.get("on_init").attach(on_init)
