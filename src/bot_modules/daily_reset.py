import datetime
import config
import util
import hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    hook.Hook.get("on_reset").attach(on_reset)
    hook.Hook.get("before_reset").attach(before_reset)


async def before_reset():
    for guild in client.guilds:
        active_channel = config.get_guild_config(guild)["active_channel"]
        channel = guild.get_channel(active_channel)
        if channel is not None and channel.permissions_for(guild.me).send_messages:
            await channel.trigger_typing()


async def on_reset():
    message_string = get_reset_message(datetime.datetime.utcnow().weekday())
    for guild in client.guilds:
        active_channel = config.get_guild_config(guild)["active_channel"]
        channel = guild.get_channel(active_channel)
        if channel is not None and channel.permissions_for(guild.me).send_messages:
            await channel.send(message_string)


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

    void_sched = config.get_global_config()["void_battle_schedule"]
    void_order = void_sched["order"]
    void_available = void_sched["availability"]
    daily_battles = [battle for battle in void_order if void_available[battle][day]]

    message_string = "It's time for the daily reset!\n" +\
        "Expert difficulty is available in " + ruins_available[day] + "!\n" +\
        "Today's Void Battles are " + util.readable_list(daily_battles) + "!"

    return message_string


hook.Hook.get("on_init").attach(on_init)
