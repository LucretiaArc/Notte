import util
import calendar
import logging
import data
import hook
import datetime

logger = logging.getLogger(__name__)

gift_string = None


async def on_init(discord_client):
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

    reset_day = get_reset_day()

    if reset_day >= 5:
        gift_target = "your favourite dragon! " + util.get_emote("notte_smile")
    else:
        gift = data.DragonGift(reset_day + 1)

        dragons = [
            d for d in data.Dragon.get_all() if
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


def get_reset_day():
    """
    Returns the weekday of the most recent reset.
    :return: The weekday of the most recent reset, from 0 to 6. 0 is Monday, 6 is Sunday.
    """
    utc_now = datetime.datetime.utcnow()
    utc_today_reset = utc_now.replace(hour=6, minute=0, second=0, microsecond=0)
    return (utc_now.weekday() - (1 if utc_now < utc_today_reset else 0)) % 7


hook.Hook.get("on_init").attach(on_init)
