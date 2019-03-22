import discord
import os
import logging
import bot_modules
import json
import util
from hook import Hook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = discord.Client()
bot_modules.import_modules()
initialised = False


# load and check config file
with open("config.json") as file:
    config = json.load(file)


# Standard events:
# on_init(client:discord.Client, config:dict)
# on_ready()
# on_message(message:discord.Message)
# on_message_private(message:discord.Message)
# on_reset()
# before_reset()
# Command events:
# public!COMMAND(message:discord.Message, args:string)
# admin!COMMAND(message:discord.Message, args:string)


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
        if message.content.startswith(config["token"]):
            command = message.content.split(" ")[0][len(config["token"]):].lower()  # just command text
            args = message.content[len(config["token"]) + len(command) + 1:]
            if Hook.exists("public!"+command):
                await Hook.get("public!"+command)(message, args)
            elif message.channel.is_private and message.author.id == config["owner"] and Hook.exists("admin!"+command):
                await Hook.get("admin!"+command)(message, args)
            else:
                await client.send_message(message.channel, "I don't know that command, sorry!")
        else:
            await Hook.get("on_message")(message)
            if message.channel.is_private:
                await Hook.get("on_message_private")(message)


util.create_daily_hook("on_reset", 6, 0, 1)
util.create_daily_hook("before_reset", 5, 59, 54)


client.run(os.environ["DISCORD_CLIENT_TOKEN"])
