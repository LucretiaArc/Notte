import util
from hook import Hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    Hook.get("on_message").attach(handle_message)


async def handle_message(message):
    responses = {
        "thanks notte": "You're welcome!",
        "what is bog?": util.get_emote("bog") + " **Bog** is an affliction which reduces movement speed by 50% and increases damage received by 50% for a limited amount of time."
    }
    content = message.content.lower()
    for response in responses:
        if response in content:
            await client.send_message(message.channel, responses[response])


Hook.get("on_init").attach(on_init)
