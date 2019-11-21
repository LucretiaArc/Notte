import datetime
import config
import hook
import discord

client: discord.Client = None


async def on_init(discord_client):
    global client
    client = discord_client

    hook.Hook.get("on_reset").attach(on_reset)
    hook.Hook.get("before_reset").attach(before_reset)


async def before_reset():
    for guild in client.guilds:
        active_channel = config.get_guild(guild).active_channel
        channel = guild.get_channel(active_channel)
        if channel is not None and channel.permissions_for(guild.me).send_messages:
            await channel.trigger_typing()


async def on_reset():
    message_string = get_reset_message(datetime.datetime.utcnow())
    for guild in client.guilds:
        active_channel = config.get_guild(guild).active_channel
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
        f"Expert difficulty is available in {ruins_available[date.weekday()]}!",
        ""  # separate conditional lines from constant lines
    ]

    # monthly resets
    if date.day == 1:
        message_lines.append("The Void Battle and Astral Raid treasure trades have been reset!")
    elif date.day == 15:
        message_lines.append("The Mercurial Gauntlet Victor's Trove has been reset!")

    return "\n".join(message_lines).strip()


hook.Hook.get("on_init").attach(on_init)
