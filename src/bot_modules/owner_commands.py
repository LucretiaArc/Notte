import discord
import config
import json
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
        await client.send_message(client.get_channel(channel), output_message)
    except discord.Forbidden:
        await client.send_message(message.channel, "I don't have permission to send messages in that channel. Sorry!")


async def get_config(message, args):
    config_json = json.dumps(dict(config.get_server_config(args.strip())), indent=2, sort_keys=True)
    await client.send_message(message.channel, "```json\n{0}\n```".format(config_json))


async def inspect_configs(message, args):
    config_json = json.dumps(dict(config.Config.inspect_server_configs()), indent=2, sort_keys=True)
    await client.send_message(message.channel, "```json\n{0}\n```".format(config_json))


Hook.get("on_init").attach(on_init)
