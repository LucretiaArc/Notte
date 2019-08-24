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
    hook.Hook.get("owner!inspect_configs").attach(inspect_configs)
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
    config_json = json.dumps(dict(config.get_guild_config(client.get_guild(util.safe_int(args.strip(), 0)))), indent=2, sort_keys=True)
    await message.channel.send("```json\n{0}\n```".format(config_json))


async def inspect_configs(message, args):
    guild_config_json = json.dumps(dict(config.Config.inspect_guild_configs()), indent=2, sort_keys=True)
    writable_config_json = json.dumps(dict(config.get_wglobal_config()), indent=2, sort_keys=True)
    msg_str = "```json\ngc = {0}\n\nwc = {1}\n```".format(guild_config_json, writable_config_json)
    await util.send_long_message_as_file(message.channel, msg_str)


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

    wconfig = config.get_wglobal_config()
    wconfig[key] = value
    config.set_wglobal_config(wconfig)
    await message.channel.send('Updated config["{0}"] = {1}'.format(key, json.dumps(value)))


async def wconfig_del(message, args):
    key = args.strip()
    wconfig = config.get_wglobal_config()
    if key in wconfig:
        wconfig.pop(key)
    else:
        await message.channel.send("No such configuration key: " + key)
        return

    if key in config.Config.wc_default:
        wconfig[key] = config.Config.wc_default[key]
        msg = 'Updated config["{0}"] = {1}'.format(key, json.dumps(config.Config.wc_default[key]))
    else:
        msg = 'Deleted config["{0}"]'.format(key)

    config.set_wglobal_config(wconfig)
    await message.channel.send(msg)


hook.Hook.get("on_init").attach(on_init)
