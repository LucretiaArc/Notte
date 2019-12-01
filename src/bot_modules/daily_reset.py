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
    hdt_available = [
        "High **Midgardsormr**'s Trial and High **Mercury**'s Trial",
        "High **Brunhilda**'s Trial and High **Zodiark**'s Trial",
        "High **Mercury**'s Trial and High **Jupiter**'s Trial",
        "High **Midgardsormr**'s Trial and High **Zodiark**'s Trial",
        "High **Brunhilda**'s Trial and High **Jupiter**'s Trial",
        "all High Dragon Trials",
        "all High Dragon Trials"
    ]

    if date.tzinfo:
        date = date.astimezone(datetime.timezone.utc)

    message_lines = [
        "It's time for the daily reset!",
        f"Master difficulty is available in {hdt_available[date.weekday()]}!",
        ""  # separate conditional lines from constant lines
    ]

    # monthly resets
    if date.day == 1:
        message_lines.append("The Void Battle and Astral Raid treasure trades have been reset!")
    elif date.day == 15:
        message_lines.append("The Mercurial Gauntlet Victor's Trove has been reset!")

    return "\n".join(message_lines).strip()


hook.Hook.get("on_init").attach(on_init)
