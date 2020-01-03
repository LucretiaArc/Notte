import discord
import asyncio
import random
import config
import hook

client = None
statuses = []


async def on_init(discord_client):
    global client, statuses
    client = discord_client
    statuses = list(zip(*(config.get_global("status"))))
    change_status("my favourites!")


def change_status(new_status=None):
    new_status = new_status or random.choices(statuses[0], weights=statuses[1])[0]
    asyncio.ensure_future(client.change_presence(activity=discord.Game(new_status)))
    asyncio.get_event_loop().call_later(600, change_status)


hook.Hook.get("on_init").attach(on_init)
