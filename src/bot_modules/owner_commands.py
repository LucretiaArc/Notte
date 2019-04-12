import discord
import config
import json
import util
import re
from hook import Hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    Hook.get("owner!say").attach(say)
    Hook.get("owner!getconfig").attach(get_config)
    Hook.get("owner!inspectconfigs").attach(inspect_configs)
    Hook.get("owner!voidschedule").attach(void_schedule_format)


async def say(message, args):
    channel = args.split(" ")[0]
    output_message = args[len(channel) + 1:]
    try:
        await client.get_channel(util.safe_int(channel, None)).send(output_message)
    except discord.Forbidden:
        await message.channel.send("I don't have permission to send messages in that channel. Sorry!")
    except AttributeError:
        await message.channel.send("I couldn't find that channel. Sorry!")


async def get_config(message, args):
    config_json = json.dumps(dict(config.get_guild_config(client.get_guild(util.safe_int(args.strip(), 0)))), indent=2, sort_keys=True)
    await message.channel.send("```json\n{0}\n```".format(config_json))


async def inspect_configs(message, args):
    config_json = json.dumps(dict(config.Config.inspect_guild_configs()), indent=2, sort_keys=True)
    await message.channel.send("```json\n{0}\n```".format(config_json))


async def void_schedule_format(message, args):
    content = args.strip().replace("\u2714", "Y")
    battle_order = []
    battle_availability = {}
    for line in content.split("\n"):
        cells = list(map(str.strip, re.split(r"\s{2,}", line)))
        name = cells[0]
        days = [c != "X" for c in cells[1:]]
        if days != [True]*7:
            battle_order.append(name)
            battle_availability[name] = days

    output_message = '"order": ' + json.dumps(battle_order, indent=2) + ',\n"availability": {\n'
    availability_segements = []
    for k, v in battle_availability.items():
        availability_segements.append('  "{0}": [{1}]'.format(k, ", ".join(str(i).lower() for i in v)))
    output_message += ",\n".join(availability_segements)
    output_message += "\n}"
    await message.channel.send(output_message)


Hook.get("on_init").attach(on_init)
