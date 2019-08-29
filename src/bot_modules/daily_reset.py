import datetime
import config
import util
import hook
import re
import aiohttp
import json
import discord
import calendar

client: discord.Client = None
void_order = []
void_availability = {}


async def on_init(discord_client):
    global client, void_order, void_availability
    client = discord_client

    wc = config.get_wglobal_config()
    void_order = wc["void_order"]
    void_availability = wc["void_availability"]

    await update_void_schedule()

    hook.Hook.get("on_reset").attach(on_reset)
    hook.Hook.get("before_reset").attach(before_reset)
    hook.Hook.get("download_data").attach(update_void_schedule)


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
    global void_order, void_availability
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
    daily_battles = [battle for battle in void_order if void_availability[battle][date.weekday()]]
    message_lines.append(f"Today's Void Battles are {util.readable_list(daily_battles)}!")

    # separate occasional lines from constant lines
    message_lines.append("")

    # mercurial gauntlet reset
    if date.day == 1:
        message_lines.append("The Void Battle Treasure Trade has been reset!")
    elif date.day == 15:
        message_lines.append("The Mercurial Gauntlet Victor's Trove has been reset!")

    return "\n".join(message_lines).strip()


async def update_void_schedule():
    global void_availability, void_order
    url = "https://dragalialost.gamepedia.com/api.php?action=expandtemplates&format=json&prop=wikitext" \
          "&text={{Void/{{Void/current}}}}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response_json = await response.json(content_type=None)
            response_text = response_json["expandtemplates"]["wikitext"]
            battle_schedules = util.clean_wikitext(response_text).split("19px|middle|link= ")[1:]

            new_order = []
            new_availability = {}
            for battle in battle_schedules:
                battle_name = re.sub(r"[\u2714\u2718].*", "", battle).strip()
                battle_schedule = re.sub(r"(?:^[^\u2714\u2718]+)|\s", "", battle).strip()
                new_order.append(battle_name)
                new_availability[battle_name] = [c == "\u2714" for c in battle_schedule]

    existing_availability_str = json.dumps(void_availability)
    new_availability_str = json.dumps(new_availability)
    if existing_availability_str != new_availability_str:
        wc = config.get_wglobal_config()
        void_order = new_order
        void_availability = new_availability
        wc["void_order"] = void_order
        wc["void_availability"] = void_availability
        config.set_wglobal_config(wc)

        output_message = "Updated Void Schedule:\n"
        for i, day in enumerate(calendar.day_name):
            battles = [battle for battle in void_order if void_availability[battle][i]]
            output_message += f"{day}: {util.readable_list(battles)}\n"

        channel = client.get_channel(config.get_global_config()["logging_channel"])
        await util.send_long_message_as_file(channel, output_message, "void_schedule.txt")


hook.Hook.get("on_init").attach(on_init)
