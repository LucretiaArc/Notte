import discord
import os
import logging
import bot_modules
import util
import config
import data

from hook import Hook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = discord.Client()
bot_modules.import_modules()
initialised = False

config.Config.init_configuration()

# Standard events:
# on_init(client:discord.Client)
# on_ready()
# on_guild_join(guild:discord.Guild)
# on_message(message:discord.Message)
# on_message_private(message:discord.Message)
# on_mention(message:discord.Message)
# on_reset()
# before_reset()
# download_data()
#
# Command events:
# public!COMMAND(message:discord.Message, args:string)
# admin!COMMAND(message:discord.Message, args:string)
# owner!COMMAND(message:discord.Message, args:string)


@client.event
async def on_ready():
    global initialised
    if not initialised:
        await data.update_repositories()
        await Hook.get("on_init")(client)
        initialised = True
        logger.info(client.user.name + "'s ready to go!")

    await Hook.get("on_ready")()


@client.event
async def on_message(message: discord.Message):
    if not message.author.bot and (isinstance(message.channel, discord.abc.PrivateChannel) or message.channel.permissions_for(message.guild.me).send_messages):
        prefix = config.get_prefix(message.guild)
        if message.content.startswith(prefix):
            if not initialised:
                await message.channel.send("I've only just woken up, give me a second please!")
                return
            command = message.content[len(prefix):].split(" ")[0].lower()  # just command text
            args = message.content[len(prefix) + len(command) + 1:]
            if Hook.exists("public!"+command) and util.check_command_permissions(message, "public"):
                await Hook.get("public!"+command)(message, args)
            elif Hook.exists("admin!"+command) and util.check_command_permissions(message, "admin"):
                await Hook.get("admin!"+command)(message, args)
            elif Hook.exists("owner!"+command) and util.check_command_permissions(message, "owner"):
                await Hook.get("owner!"+command)(message, args)
            else:
                await message.channel.send("I don't know that command, sorry! Use the `help` command for a list of commands.")
        else:
            if not initialised:
                return
            await Hook.get("on_message")(message)
            if discord.utils.find(lambda m: m.id == client.user.id, message.mentions) is not None:
                await Hook.get("on_mention")(message)
            if isinstance(message.channel, discord.abc.PrivateChannel):
                await Hook.get("on_message_private")(message)


@client.event
async def on_guild_join(guild: discord.Guild):
    await Hook.get("on_guild_join")(guild)


util.create_daily_hook("on_reset", 6, 0, 1)
util.create_daily_hook("before_reset", 5, 59, 54)
util.create_daily_hook("download_data", 5, 59, 0)


client.run(os.environ["DISCORD_CLIENT_TOKEN"])
