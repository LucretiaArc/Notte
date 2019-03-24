import config
import copy
import util
from hook import Hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    Hook.get("admin!token").attach(set_token)
    Hook.get("admin!channel").attach(set_active_channel)
    Hook.get("on_mention").attach(reset_token)


def get_editable_server_config(server_id):
    return copy.deepcopy(config.get_server_config(server_id).copy())


async def set_token(message, args):
    """
    Sets the bot's token for this server. The token is the character (or characters) that come before every command.
    e.g. running `token $` means that to use the `help` command, you now have to type `$help`.
    The default token is `!!`, and you can always reset the token by mentioning the bot along with the words `reset token`
    """
    new_token = args.strip()
    if len(new_token) > 250:
        await client.send_message(message.channel, "That's too long! Try something shorter.")
        return

    if new_token == client.user.mention:
        new_token += " "

    new_config = get_editable_server_config(message.server.id)
    new_config["token"] = new_token
    config.set_server_config(message.server.id, new_config)
    await client.send_message(message.channel, "Token has been set to `{0}`".format(new_token))


async def set_active_channel(message, args):
    """
    Sets this channel as the bot's "active channel", the location where the bot sends reset messages and reminders.
    Use `channel none` to disable reset messages and reminders.
    """
    new_config = get_editable_server_config(message.server.id)
    if args.strip().lower() == "none":
        new_config["active_channel"] = ""
        config.set_server_config(message.server.id, new_config)
        await client.send_message(message.channel, "Active channel has been disabled, I won't post reset messages anymore!".format(message.channel.mention))
    else:
        new_config["active_channel"] = message.channel.id
        config.set_server_config(message.server.id, new_config)
        await client.send_message(message.channel, "Active channel has been updated, I'll post reset messages in here from now on!".format(message.channel.mention))


async def reset_token(message):
    if "reset token" in message.content.lower():
        if util.check_command_permissions(message, "admin"):
            await set_token(message, "!!")
        else:
            await client.send_message(message.channel, "You're not allowed to do that!")

Hook.get("on_init").attach(on_init)
