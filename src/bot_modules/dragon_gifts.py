import util
import json
import urllib.parse
import urllib.request
import calendar

from hook import Hook

client = None
config = None
gift_string = None


def on_init(discord_client, module_config):
    global client, config, gift_string
    client = discord_client
    config = module_config
    gift_string = retrieve_gift_string()

    Hook.get("on_reset").attach(retrieve_gift_string)
    Hook.get("public!gift").attach(gift_message)


async def gift_message(message, args):
    await client.send_message(message.channel, gift_string)


def retrieve_gift_string():
    global gift_string

    reset_day = util.get_reset_day()

    if reset_day >= 5:
        gift_target = "your favourite dragon!"
    else:
        request = "https://dragalialost.gamepedia.com/api.php?action=cargoquery&tables=Dragons&format=json&limit=500" \
                  "&fields=FullName" \
                  "&order_by=Rarity+DESC,+ElementalTypeId+ASC,+Id+DESC,+FullName+ASC" \
                  "&where=FavoriteType%3D" + str(reset_day + 1)

        with urllib.request.urlopen(request) as response:
            dragon_info_list = json.loads(response.read().decode())["cargoquery"]
            dragon_names = map(lambda d: "*" + d["title"]["FullName"] + "*", dragon_info_list)
            gift_target = "one of these dragons:\n" + "\n".join(dragon_names)

    return "It's " + calendar.day_name[reset_day] + ", so give your best gift to " + gift_target


Hook.get("on_init").attach(on_init)
