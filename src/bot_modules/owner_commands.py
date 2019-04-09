import discord
import config
import json
import util
from hook import Hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    Hook.get("owner!say").attach(say)
    Hook.get("owner!getconfig").attach(get_config)
    Hook.get("owner!inspectconfigs").attach(inspect_configs)


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


Hook.get("on_init").attach(on_init)
