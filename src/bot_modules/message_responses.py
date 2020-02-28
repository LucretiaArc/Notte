import util
import hook


async def on_init(discord_client):
    hook.Hook.get("on_message").attach(handle_message)


async def handle_message(message):
    responses = {
        "thanks notte": util.get_emote("notte_smile") + " You're welcome!",
        "what is bog?": util.get_emote("bog") + " **Bog** is an affliction which reduces movement speed by 50% and increases damage received by 50% for a limited amount of time."
    }
    content = message.content.lower()
    for response in responses:
        if response in content:
            await message.channel.send(responses[response])


hook.Hook.get("on_init").attach(on_init)
