import config
import util
import logging
import hook

logger = logging.getLogger(__name__)

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    hook.Hook.get("admin!prefix").attach(set_prefix)
    hook.Hook.get("admin!channel").attach(set_active_channel)
    hook.Hook.get("on_mention").attach(reset_prefix)


async def set_prefix(message, args):
    """
    Sets the bot's prefix for this server. The prefix is the character (or characters) that come before every command.
    e.g. running `prefix $` means that to use the `help` command, you now have to type `$help`.
    The default prefix is `!!`, and you can always reset the prefix by mentioning the bot along with the words `reset prefix`
    """
    new_prefix = args.strip()
    if len(new_prefix) > 250:
        await message.channel.send("That's too long! Try something shorter.")
        return
    if not new_prefix:
        await message.channel.send("You need to choose something to set as the prefix!")
        return
    if new_prefix == client.user.mention:
        new_prefix += " "

    guild = message.guild
    new_config = config.get_guild(guild)
    new_config.token = new_prefix
    await config.set_guild(guild, new_config)

    logger.info(f'Prefix for guild {guild.id} set to "{new_prefix}"')
    await message.channel.send(f"Prefix has been set to `{new_prefix}`")


async def set_active_channel(message, args):
    """
    Sets this channel as the bot's "active channel", the location where the bot sends reset messages and news.
    Use `channel none` to disable reset messages and reminders.
    """
    new_config = config.get_guild(message.guild)
    if args.strip().lower() == "none":
        new_config.active_channel = 0
        await config.set_guild(message.guild, new_config)
        logger.info(f"Active channel for guild {message.guild.id} disabled")
        await message.channel.send("Active channel has been disabled, I won't post reset messages anymore!")
    else:
        new_config.active_channel = message.channel.id
        await config.set_guild(message.guild, new_config)
        logger.info(f"Active channel for guild {message.guild.id} set to {message.channel.id}")
        await message.channel.send("Active channel has been updated, I'll post reset messages in here from now on!")


async def reset_prefix(message):
    if "reset prefix" in message.content.lower() and util.check_command_permissions(message, "admin"):
        await set_prefix(message, "!!")
        logger.info(f"Prefix for guild {message.guild.id} reset")

hook.Hook.get("on_init").attach(on_init)
