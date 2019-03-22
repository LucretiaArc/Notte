import discord
import asyncio
import util
import datetime
from hook import Hook

import logging
logger = logging.getLogger(__name__)

client = None
config = None


def schedule_reset_message():
    asyncio.ensure_future(util.schedule_at_time(prepare_reset, 5, 59, 55))
    asyncio.ensure_future(util.schedule_at_time(on_reset, 6, 0, 1))


async def on_init(discord_client, module_config):
    global client, config
    client = discord_client
    config = module_config

    schedule_reset_message()


def prepare_reset():
    for channel in config["active_channels"]:
        asyncio.ensure_future(client.send_typing(discord.Object(channel)))


def on_reset():
    message_string = get_reset_message(datetime.datetime.utcnow().weekday())
    for channel in config["active_channels"]:
        asyncio.ensure_future(client.send_message(discord.Object(channel), message_string))

    schedule_reset_message()
    logger.info("Posted and scheduled reset message")


def get_reset_message(day):
    ruins_available = [
        "all Elemental Ruins",
        "Flamehowl Ruins",
        "Waterscour Ruins",
        "Windmaul Ruins",
        "Lightsunder Ruins",
        "Shadowsteep Ruins",
        "all Elemental Ruins"
    ]

    # different void battles through march 30th, after which these are the rotations
    # void_battles_available = [
    #     "Steel Golem and Blazing Ghost",
    #     "Raging Manticore and Obsidian Golem",
    #     "Steel Golem and Frost Hermit",
    #     "Void Zephyr and Obsidian Golem",
    #     "Steel Golem and Blazing Ghost",
    #     "Raging Manticore, Void Zephyr, and Frost Hermit",
    #     "Steel Golem, Void Zephyr, Frost Hermit, Obsidian Golem, and Blazing Ghost"
    # ]

    void_battles_available = [
        "Steel Golem, Obsidian Golem, and Blazing Ghost",
        "Raging Manticore, Frost Hermit, and Blazing Ghost",
        "Steel Golem, Void Zephyr, Frost Hermit, and Obsidian Golem",
        "Raging Manticore, Frost Hermit, Obsidian Golem, and Blazing Ghost",
        "Steel Golem, Frost Hermit, and Blazing Ghost",
        "Raging Manticore, Void Zephyr, Frost Hermit, and Obsidian Golem",
        "Steel Golem, Void Zephyr, Frost Hermit, Obsidian Golem, and Blazing Ghost"
    ]

    message_string = "It's time for the daily reset!\n" +\
        "Expert difficulty is available in " + ruins_available[day] + "!\n" +\
        "Today's Void Battles are " + void_battles_available[day] + "!"

    return message_string


Hook.get("on_init").attach(on_init)
