import logging
import asyncio
import discord
import config
import io


class DiscordHandler(logging.Handler):
    def __init__(self, channel: discord.abc.Messageable):
        super().__init__()
        self.channel = channel

    def emit(self, record):
        async def send_log(future):
            # noinspection PyBroadException
            try:
                await future
            except Exception:
                # This may occur if the cause of the exception was a disconnection from Discord.
                # Therefore, attempting to log the exception to discord might cause further unknown exceptions.
                # We don't need to do anything if this happens, because we should be using a real handler as well.
                pass

        msg = "```\n{0}\n```".format(self.format(record))
        if len(msg) <= 2000:
            fut = self.channel.send(msg)
        else:
            fut = self.channel.send(
                "An exception occurred!",
                file=discord.File(fp=io.BytesIO(bytes(msg, "UTF-8")), filename="log.txt")
            )

        asyncio.ensure_future(send_log(fut))


def configure_console():
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.NOTSET)
    console_handler.setFormatter(logging.Formatter("%(levelname)-8s %(name)s: %(message)s"))
    logging.getLogger().addHandler(console_handler)


def configure_discord(client: discord.Client):
    channel = client.get_channel(config.get_global_config()["logging_channel"])
    if channel is None:
        raise ValueError("Logging channel not found")

    discord_handler = DiscordHandler(channel)
    discord_handler.setLevel(logging.ERROR)
    discord_handler.setFormatter(logging.Formatter(
        fmt="Date: %(asctime)s\nLevel: %(levelname)s\n%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logging.getLogger().addHandler(discord_handler)

