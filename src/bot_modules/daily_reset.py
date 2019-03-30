import datetime
import config
from hook import Hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    Hook.get("on_reset").attach(on_reset)
    Hook.get("before_reset").attach(before_reset)


async def before_reset():
    for server in client.servers:
        active_channel = config.get_server_config(server.id)["active_channel"]
        channel = server.get_channel(active_channel)
        if channel is not None and channel.permissions_for(server.me).send_messages:
            await client.send_typing(channel)


async def on_reset():
    message_string = get_reset_message(datetime.datetime.utcnow().weekday())
    for server in client.servers:
        active_channel = config.get_server_config(server.id)["active_channel"]
        channel = server.get_channel(active_channel)
        if channel is not None and channel.permissions_for(server.me).send_messages:
            await client.send_message(channel, message_string)


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

    void_battles_available = [
        "Steel Golem and Blazing Ghost",
        "Raging Manticore and Obsidian Golem",
        "Steel Golem and Frost Hermit",
        "Void Zephyr and Obsidian Golem",
        "Steel Golem and Blazing Ghost",
        "Raging Manticore, Void Zephyr, and Frost Hermit",
        "Steel Golem, Void Zephyr, Frost Hermit, Obsidian Golem, and Blazing Ghost"
    ]

    message_string = "It's time for the daily reset!\n" +\
        "Expert difficulty is available in " + ruins_available[day] + "!\n" +\
        "Today's Void Battles are " + void_battles_available[day] + "!"

    return message_string


Hook.get("on_init").attach(on_init)
