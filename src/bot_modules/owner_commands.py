import discord
import config
import json
import util
import data
import hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    hook.Hook.get("owner!say").attach(say)
    hook.Hook.get("owner!get_config").attach(get_config)
    hook.Hook.get("owner!inspect_w").attach(inspect_writeable_config)
    hook.Hook.get("owner!inspect_g").attach(inspect_guild_configs)
    hook.Hook.get("owner!update_data").attach(update_data)
    hook.Hook.get("owner!wc_set").attach(wconfig_set)
    hook.Hook.get("owner!wc_del").attach(wconfig_del)


async def say(message, args):
    channel = args.split(" ")[0]
    output_message = args[len(channel) + 1:]
    try:
        await client.get_channel(util.safe_int(channel, None)).send(output_message)
    except discord.Forbidden:
        await message.channel.send("I don't have permission to send messages in that channel. Sorry!")
    except AttributeError:
        await message.channel.send("I couldn't find that channel. Sorry!")


async def get_config(message, args):
    guild = client.get_guild(util.safe_int(args.strip(), 0))
    if guild is None:
        guild = message.guild
    config_json = json.dumps(config.get_guild(guild).get_dict(), indent=2, sort_keys=True)
    await message.channel.send(f"```json\n{config_json}\n```")


async def inspect_guild_configs(message, args):
    guild_config_json = json.dumps(config.guild_config_cache, default=config.Config.get_dict, indent=2)
    await util.send_long_message_as_file(message.channel, f"```json\n{guild_config_json}\n```")


async def inspect_writeable_config(message, args):
    writable_config_json = json.dumps(config.get_writeable().get_dict(), indent=2, sort_keys=True)
    await util.send_long_message_as_file(message.channel, f"```json\n{writable_config_json}\n```")


async def update_data(message, args):
    await message.channel.send("Updating data, please wait...")
    try:
        await data.update_repositories()
    except Exception:
        await message.channel.send("There was an error updating the data. Check the logs for details!")
        raise
    else:
        await message.channel.send("Updated data successfully.")


async def wconfig_set(message, args):
    key = args.split(" ")[0]
    try:
        value = json.loads(args[len(key) + 1:])
    except json.decoder.JSONDecodeError:
        await message.channel.send("Bad config value, must be valid JSON")
        return

    wc = config.get_writeable()
    try:
        setattr(wc, key, value)
    except ValueError:
        await message.channel.send(f"Invalid config key: {key}")
        return
    config.set_writeable(wc)
    await message.channel.send(f'Updated config["{key}"] = {json.dumps(value)}')


async def wconfig_del(message, args):
    key = args.strip()
    wc = config.get_writeable()
    if hasattr(wc, key):
        delattr(wc, key)
    else:
        await message.channel.send(f"No such configuration key: {key}")
        return

    config.set_writeable(wc)
    await message.channel.send(f"Successfully deleted key: {key}")


hook.Hook.get("on_init").attach(on_init)
