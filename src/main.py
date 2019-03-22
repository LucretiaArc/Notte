import discord
import os
import logging
import bot_modules
import json
from hook import Hook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = discord.Client()
bot_modules.import_modules()
initialised = False


# load and check config file
with open("config.json") as file:
    config = json.load(file)


# Hookable events:
# on_init(discord.Client, config dict)
# on_ready()
# on_message(discord.Message)
# on_message_private(discord.Message)

@client.event
async def on_ready():
    global initialised
    if not initialised:
        initialised = True
        logger.info(client.user.name + "'s ready to go!")
        await Hook.get("on_init")(client, config)

    await Hook.get("on_ready")()


@client.event
async def on_message(message):
    if not message.author.bot:
        await Hook.get("on_message")(message)
        if message.channel.is_private:
            await Hook.get("on_message_private")(message)


client.run(os.environ["DISCORD_CLIENT_TOKEN"])
