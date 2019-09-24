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
    await message.channel.send("```json\n{0}\n```".format(config_json))


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
        await message.channel.send("Invalid config key")
        return
    await config.set_writeable(wc)
    await message.channel.send('Updated config["{0}"] = {1}'.format(key, json.dumps(value)))


async def wconfig_del(message, args):
    key = args.strip()
    wc = config.get_writeable()
    if key in wc:
        delattr(wc, key)
    else:
        await message.channel.send("No such configuration key: " + key)
        return

    await config.set_writeable(wc)
    await message.channel.send(f"Successfully deleted key {key}")


hook.Hook.get("on_init").attach(on_init)
