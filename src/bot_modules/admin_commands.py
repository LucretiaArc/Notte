import config
import util
from hook import Hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    Hook.get("admin!token").attach(set_token)
    Hook.get("admin!channel").attach(set_active_channel)
    Hook.get("on_mention").attach(reset_token)


async def set_token(message, args):
    """
    Sets the bot's token for this server. The token is the character (or characters) that come before every command.
    e.g. running `token $` means that to use the `help` command, you now have to type `$help`.
    The default token is `!!`, and you can always reset the token by mentioning the bot along with the words `reset token`
    """
    new_token = args.strip()
    if len(new_token) > 250:
        await message.channel.send("That's too long! Try something shorter.")
        return

    if new_token == client.user.mention:
        new_token += " "

    new_config = config.get_guild_config_editable(message.guild)
    new_config["token"] = new_token
    config.set_guild_config(message.guild, new_config)
    await message.channel.send("Token has been set to `{0}`".format(new_token))


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


async def reset_token(message):
    if "reset token" in message.content.lower():
        if util.check_command_permissions(message, "admin"):
            await set_token(message, "!!")
        else:
            await message.channel.send("You're not allowed to do that!")

Hook.get("on_init").attach(on_init)
