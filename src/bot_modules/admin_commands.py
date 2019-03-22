import discord
from hook import Hook

client = None


async def on_init(discord_client, module_config):
    global client
    client = discord_client


async def say(message, args):
    channel = args.split(" ")[0]
    output_message = args[len(channel) + 1:]
    await client.send_message(discord.Object(channel), output_message)


Hook.get("on_init").attach(on_init)
Hook.get("admin!say").attach(say)
