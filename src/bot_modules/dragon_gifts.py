import util
import aiohttp
import calendar
import logging
from hook import Hook

logger = logging.getLogger(__name__)

client = None
gift_string = None


async def on_init(discord_client):
    global client
    client = discord_client

    Hook.get("on_reset").attach(update_gift_string)
    Hook.get("public!gift").attach(gift_message)

    await update_gift_string()


async def gift_message(message, args):
    """
    Provides details about the dragons who receive and extra bonus from today's gift in the Dragon Roost.
    """
    await client.send_message(message.channel, gift_string)


async def update_gift_string():
    global gift_string

    reset_day = util.get_reset_day()

    if reset_day >= 5:
        gift_target = "your favourite dragon!"
    else:
        logger.info("Requesting today's preferred dragons")
        url = "https://dragalialost.gamepedia.com/api.php?action=cargoquery&tables=Dragons&format=json&limit=500" \
              "&fields=FullName,Rarity,ElementalTypeId" \
              "&order_by=Rarity+DESC,+ElementalTypeId+ASC,+Id+DESC,+FullName+ASC" \
              "&where=FavoriteType%3D" + str(reset_day + 1)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                gifts_json = await response.json()
                dragon_info_list = [d["title"] for d in gifts_json["cargoquery"]]
                elemental_types = ["fire", "water", "wind", "light", "dark"]

                dragon_info = []
                for d in dragon_info_list:
                    if util.safe_int(d["Rarity"], -1) == -1:
                        continue

                    if util.safe_int(d["ElementalTypeId"], -1) == -1:
                        continue

                    dragon_info.append({
                        "name": d["FullName"],
                        "emote": util.get_emote(elemental_types[int(d["ElementalTypeId"])-1]),
                        "rarity": d["Rarity"]
                    })

                current_rarity = 6
                gift_target = "one of these dragons:"
                for dragon in dragon_info:
                    gift_target += "\n"
                    if int(dragon["rarity"]) < current_rarity:
                        current_rarity = int(dragon["rarity"])
                        gift_target += "\n" + current_rarity * util.get_emote("rarity"+str(current_rarity)) + "\n"

                    gift_target += dragon["emote"] + " " + dragon["name"]

    gift_string = "It's " + calendar.day_name[reset_day] + ", so give your best gift to " + gift_target

    logger.info("Finished requesting today's preferred dragons")


Hook.get("on_init").attach(on_init)
