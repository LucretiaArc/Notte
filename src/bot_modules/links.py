import hook
import logging

logger = logging.getLogger(__name__)

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    hook.Hook.get("public!void").attach(void_schedule)
    hook.Hook.get("public!mg").attach(mercurial_gauntlet)
    hook.Hook.get("public!issues").attach(ongoing_issues)
    hook.Hook.get("public!calc").attach(unit_calculator)
    hook.Hook.get("public!sim").attach(dps_simulator)


async def void_schedule(message, args):
    """Links to the void battle schedule."""
    await message.channel.send("<https://dragalialost.com/en/news/detail/19999>")


async def mercurial_gauntlet(message, args):
    """Links to the mercurial gauntlet endeavour list."""
    await message.channel.send("<https://dragalialost.com/en/news/detail/20000>")


async def ongoing_issues(message, args):
    """Links to the list of ongoing issues within the game."""
    await message.channel.send("<https://dragalialost.com/en/news/detail/213>")


async def unit_calculator(message, args):
    """Links to the unit calculator."""
    await message.channel.send("<https://dragalialost.info/stats/en>")


async def dps_simulator(message, args):
    """Links to the DPS simulator."""
    await message.channel.send("<https://mushymato.github.io/dl-sim-vue/>")


hook.Hook.get("on_init").attach(on_init)
