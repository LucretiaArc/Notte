from hook import Hook
import discord

client = None


async def on_init(discord_client, module_config):
    global client
    client = discord_client


async def handle_commands(message):
    if message.author.id != "126587545336283136":
        return

    args = message.content.split(" ")

    cmd = args[0]
    if cmd == "say":
        await client.send_message(discord.Object(args[1]), " ".join(args[2:]))


Hook.get("on_init").attach(on_init)
Hook.get("on_message_private").attach(handle_commands)
