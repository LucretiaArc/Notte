import config
import copy
from hook import Hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    Hook.get("admin!token").attach(set_token)
    Hook.get("admin!channel").attach(set_active_channel)


def get_editable_server_config(server_id):
    return copy.deepcopy(config.get_server_config(server_id).copy())


async def set_token(message, args):
    new_token = args.strip()
    new_config = get_editable_server_config(message.server.id)
    new_config["token"] = new_token
    config.set_server_config(message.server.id, new_config)
    await client.send_message(message.channel, "Token has been set to `{0}`".format(new_token))


async def set_active_channel(message, args):
    new_config = get_editable_server_config(message.server.id)
    new_config["active_channel"] = message.channel.id
    config.set_server_config(message.server.id, new_config)
    await client.send_message(message.channel, "Active channel updated, {0} is now the active channel.".format(message.channel.mention))


Hook.get("on_init").attach(on_init)
