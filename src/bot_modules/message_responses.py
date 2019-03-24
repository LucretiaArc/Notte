from hook import Hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    Hook.get("on_message").attach(handle_message)


async def handle_message(message):
    if "thanks notte" in message.content.lower():
        await client.send_message(message.channel, "You're welcome!")


Hook.get("on_init").attach(on_init)
