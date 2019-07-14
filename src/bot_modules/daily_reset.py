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
    message_string = get_reset_message(datetime.datetime.utcnow())
    for guild in client.guilds:
        active_channel = config.get_guild_config(guild)["active_channel"]
        channel = guild.get_channel(active_channel)
        if channel is not None and channel.permissions_for(guild.me).send_messages:
            await channel.send(message_string)


def get_reset_message(date: datetime.datetime):
    ruins_available = [
        "all Elemental Ruins",
        "Flamehowl Ruins",
        "Waterscour Ruins",
        "Windmaul Ruins",
        "Lightsunder Ruins",
        "Shadowsteep Ruins",
        "all Elemental Ruins"
    ]

    if date.tzinfo:
        date = date.astimezone(datetime.timezone.utc)

    message_lines = [
        "It's time for the daily reset!",
        f"Expert difficulty is available in {ruins_available[date.weekday()]}!"
    ]

    # today's void battles
    void_sched = config.get_global_config()["void_battle_schedule"]
    void_order = void_sched["order"]
    void_available = void_sched["availability"]
    daily_battles = [battle for battle in void_order if void_available[battle][date.weekday()]]
    message_lines.append(f"Today's Void Battles are {util.readable_list(daily_battles)}!")

    # separate occasional lines from constant lines
    message_lines.append("")

    # mercurial gauntlet reset
    if date.day == 1:
        message_lines.append("The Void Battle Treasure Trade has been reset!")
    elif date.day == 15:
        message_lines.append("The Mercurial Gauntlet Victor's Trove has been reset!")

    return "\n".join(message_lines).strip()


hook.Hook.get("on_init").attach(on_init)
