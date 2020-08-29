import hook
import logging
import discord
import util
from . import core, db, image, pool, showcase_types

logger = logging.getLogger(__name__)


async def on_init(discord_client):
    db.create_db()

    hook.Hook.get("download_data_delayed").attach(image.update_entity_icons)
    hook.Hook.get("owner!update_sim_icons").attach(update_entity_icons_cmd)
    hook.Hook.get("public!tenfold").attach(tenfold_summon)
    hook.Hook.get("public!single").attach(single_summon)
    hook.Hook.get("public!showcase").attach(select_showcase)
    hook.Hook.get("public!rates").attach(rates)


async def select_showcase(message, args):
    """
    Selects a showcase to summon on. To select a showcase, use `showcase <showcase name>`.
    To select a generic showcase without any rate-up units or dragons, use `showcase none`.
    To get information about your currently selected showcase, use `showcase`.
    To get a list of showcases, use `showcase list`.

    **Note:** Showcases as represented in the summoning simulator aren't historically accurate. This means:
     - All currently available permanent adventurers and dragons are present in the non-featured pool
     - Wyrmprints aren't summonable in the showcases which featured them
     - Showcases which appeared prior to the 5★ dragon rate change on July 31st, 2019 will use the new dragon rates
    """
    args = args.strip()
    if args == "list":
        showcase_list = sorted(core.SimShowcaseCache.showcases.values(), key=lambda sc: sc.showcase.start_date, reverse=True)
        await message.channel.send(", ".join(sc.showcase.name for sc in showcase_list))
    elif not args:
        showcase_info, sim_showcase = db.get_current_showcase_info(message.channel.id, message.author.id)
        if sim_showcase == core.SimShowcaseCache.default_showcase:
            await message.channel.send(showcase_info)
        else:
            await message.channel.send(showcase_info, embed=sim_showcase.showcase.get_embed())
    else:
        sim_showcase = core.SimShowcaseCache.match(args)
        if sim_showcase:
            await message.channel.send(db.set_showcase(message.channel.id, message.author.id, sim_showcase))
        else:
            await message.channel.send("I don't know that showcase! Use `showcase list` to see the list of showcases.")


async def rates(message, args):
    """
    Shows a rate breakdown for your current banner.
    """
    await message.channel.send(db.get_rate_breakdown(message.channel.id, message.author.id))


async def tenfold_summon(message, args):
    """
    Simulates a tenfold summon on your current showcase.
    To choose a showcase to summon on, use the `showcase` command.
    """
    results, text = db.perform_tenfold_summon(message.channel.id, message.author.id)
    with image.get_image_fp(results) as fp:
        await message.channel.send(text, file=discord.File(fp, filename="result.png"))


async def single_summon(message, args):
    """
    Simulates a single summon on your current showcase.
    To choose a showcase to summon on, use the `showcase` command.
    """
    total_summons = util.safe_int(args, 1)
    if total_summons < 1:
        await message.channel.send("I don't know how to do that many!")
    elif total_summons > 10:
        await message.channel.send("You can't do more than ten singles at a time!")
    else:
        results, text = db.perform_single_summons(message.channel.id, message.author.id, total_summons)
        with image.get_image_fp(results) as fp:
            await message.channel.send(text, file=discord.File(fp, filename="result.png"))


async def update_entity_icons_cmd(message, args):
    await image.update_entity_icons()
    await message.channel.send("Updated summoning sim icons.")


hook.Hook.get("on_init").attach(on_init)
