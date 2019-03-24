import discord
import os
import logging
import bot_modules
import util
import config

from hook import Hook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = discord.Client()
bot_modules.import_modules()
initialised = False


# Standard events:
# on_init(client:discord.Client)
# on_ready()
# on_server_join(server:discord.Server)
# on_message(message:discord.Message)
# on_message_private(message:discord.Message)
# on_reset()
# before_reset()
# Command events:
# public!COMMAND(message:discord.Message, args:string)
# admin!COMMAND(message:discord.Message, args:string)
# owner!COMMAND(message:discord.Message, args:string)


@client.event
async def on_ready():
    global initialised
    if not initialised:
        initialised = True
        config.Config.init_configuration()
        await Hook.get("on_init")(client)
        logger.info(client.user.name + "'s ready to go!")

    await Hook.get("on_ready")()


@client.event
async def on_message(message):
    if not message.author.bot:
        token = config.get_response_token(message.server)
        if message.content.startswith(token):
            command = message.content.split(" ")[0][len(token):].lower()  # just command text
            args = message.content[len(token) + len(command) + 1:]
            if Hook.exists("public!"+command) and util.check_command_permissions(message, "public"):
                await Hook.get("public!"+command)(message, args)
            elif Hook.exists("admin!"+command) and util.check_command_permissions(message, "admin"):
                await Hook.get("admin!"+command)(message, args)
            elif Hook.exists("owner!"+command) and util.check_command_permissions(message, "owner"):
                await Hook.get("owner!"+command)(message, args)
            else:
                await client.send_message(message.channel, "I don't know that command, sorry! Use the `help` command for a list of commands.")
        else:
            await Hook.get("on_message")(message)
            if message.channel.is_private:
                await Hook.get("on_message_private")(message)


@client.event
async def on_server_join(server):
    await Hook.get("on_server_join")(server)


util.create_daily_hook("on_reset", 6, 0, 1)
util.create_daily_hook("before_reset", 5, 59, 54)


client.run(os.environ["DISCORD_CLIENT_TOKEN"])
