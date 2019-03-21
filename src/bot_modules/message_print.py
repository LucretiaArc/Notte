from hook import Hook

client = None


async def on_init(discord_client, module_config):
    global client
    client = discord_client


async def handle_message(message):
    if "thanks notte" in message.content.lower():
        await client.send_message(message.channel, "You're welcome!")


Hook.get("on_init").attach(on_init)
Hook.get("on_message").attach(handle_message)
