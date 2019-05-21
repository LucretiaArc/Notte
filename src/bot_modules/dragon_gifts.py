import util
import calendar
import logging
import data
import hook
import datetime

logger = logging.getLogger(__name__)

client = None
gift_string = None


async def on_init(discord_client):
    global client
    client = discord_client

    hook.Hook.get("on_reset").attach(update_gift_string)
    hook.Hook.get("public!gift").attach(gift_message)

    await update_gift_string()


async def gift_message(message, args):
    """
    Provides details about the dragons who receive and extra bonus from today's gift in the Dragon Roost.
    """
    await message.channel.send(gift_string)


async def update_gift_string():
    global gift_string

    reset_day = util.get_reset_day()

    if reset_day >= 5:
        gift_target = "your favourite dragon! " + util.get_emote("notte_smile")
    else:
        gift = data.DragonGift(reset_day + 1)

        all_dragons = data.Dragon.get_all().values()
        dragons = [
            d for d in all_dragons if
            d.favourite_gift == gift
            and d.rarity
            and d.release_date
            and d.release_date <= datetime.datetime.now(datetime.timezone.utc)
        ]

        # sorting
        dragons.sort(key=lambda d: d.full_name)  # by name
        dragons.sort(key=lambda d: d.element.value)  # by element
        dragons.sort(key=lambda d: d.rarity, reverse=True)  # by rarity

        current_rarity = 6
        gift_target = "one of these dragons:"
        for d in dragons:
            gift_target += "\n"
            if d.rarity < current_rarity:
                current_rarity = d.rarity
                gift_target += "\n" + current_rarity * util.get_emote("rarity"+str(current_rarity)) + "\n"

            gift_target += util.get_emote(d.element) + " " + d.full_name

    gift_string = "It's " + calendar.day_name[reset_day] + ", so give your best gift to " + gift_target


hook.Hook.get("on_init").attach(on_init)
