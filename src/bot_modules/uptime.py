import time
import itertools
import util
import sys
import hook
import logging
import config

logger = logging.getLogger(__name__)

client = None
start_time = time.time()


async def on_init(discord_client):
    global client
    client = discord_client

    hook.Hook.get("public!uptime").attach(uptime)
    if config.get_global("general")["enable_automatic_restart"]:
        util.create_daily_hook("automatic_restart", 12, 0, 0)
        hook.Hook.get("automatic_restart").attach(restart)


def get_uptime_string(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    time_vals = [days, hours, minutes, seconds]
    labels = ["d", "h", "m", "s"]
    label_val_pairs = list(itertools.dropwhile(lambda p: p[0] == 0, zip(time_vals, labels)))
    return " ".join(f"{v}{l}" for v, l in label_val_pairs)


async def uptime(message, args):
    dt = round(time.time() - start_time)
    await message.channel.send(str(get_uptime_string(dt)))


def restart():
    dt = time.time() - start_time
    if dt > 3600:
        logger.info("Performing automatic restart")
        sys.exit(0)
    else:
        logger.info("Skipping automatic restart")


hook.Hook.get("on_init").attach(on_init)
