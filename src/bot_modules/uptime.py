import time
import itertools
import hook
import logging

logger = logging.getLogger(__name__)

start_time = time.time()


async def on_init(discord_client):
    global start_time
    start_time = time.time()
    hook.Hook.get("owner!uptime").attach(uptime)


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


hook.Hook.get("on_init").attach(on_init)
