import config
import util
import hook

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

    if new_prefix == client.user.mention:
        new_prefix += " "

    new_config = config.get_guild_config_editable(message.guild)
    new_config["token"] = new_prefix
    config.set_guild_config(message.guild, new_config)
    await message.channel.send("Prefix has been set to `{0}`".format(new_prefix))


async def set_active_channel(message, args):
    """
    Sets this channel as the bot's "active channel", the location where the bot sends reset messages and reminders.
    Use `channel none` to disable reset messages and reminders.
    """
    new_config = config.get_guild_config_editable(message.guild)
    if args.strip().lower() == "none":
        new_config["active_channel"] = 0
        config.set_guild_config(message.guild, new_config)
        await message.channel.send("Active channel has been disabled, I won't post reset messages anymore!".format(message.channel.mention))
    else:
        new_config["active_channel"] = message.channel.id
        config.set_guild_config(message.guild, new_config)
        await message.channel.send("Active channel has been updated, I'll post reset messages in here from now on!".format(message.channel.mention))


async def reset_prefix(message):
    if "reset prefix" in message.content.lower():
        if util.check_command_permissions(message, "admin"):
            await set_prefix(message, "!!")
        else:
            await message.channel.send("You're not allowed to do that!")

hook.Hook.get("on_init").attach(on_init)
