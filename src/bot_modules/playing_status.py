import discord
import asyncio
import random
import config
import hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client
    change_status()


def change_status():
    statuses = list(zip(*(config.get_global_config()["random_statuses"])))
    new_status = random.choices(statuses[0], weights=statuses[1])[0]
    asyncio.ensure_future(client.change_presence(activity=discord.Game(new_status)))
    asyncio.get_event_loop().call_later(600, change_status)


hook.Hook.get("on_init").attach(on_init)
