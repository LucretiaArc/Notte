import discord
import asyncio
import random
import config
from hook import Hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client
    change_status()


def change_status():
    statuses = list(zip(*(config.get_global_config()["random_statuses"])))
    new_status = random.choices(statuses[0], weights=statuses[1])[0]
    asyncio.ensure_future(client.change_presence(game=discord.Game(name=new_status)))
    asyncio.get_event_loop().call_later(600, change_status)


Hook.get("on_init").attach(on_init)
