import logging
import asyncio
import discord
import config


class DiscordHandler(logging.Handler):
    def __init__(self, channel: discord.abc.Messageable):
        super().__init__()
        self.channel = channel

    def emit(self, record):
        msg = "```\n{0}\n```".format(self.format(record))
        fut = self.channel.send(msg)
        asyncio.ensure_future(fut)


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

