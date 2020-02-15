import hook
import logging
import io
import discord
from PIL import Image
from . import core, db, icons

logger = logging.getLogger(__name__)


async def on_init(discord_client):
    db.create_db()

    hook.Hook.get("public!tenfold").attach(tenfold_summon)
    hook.Hook.get("public!single").attach(single_summon)
    hook.Hook.get("public!showcase").attach(select_showcase)


async def select_showcase(message, args):
    """
    Selects a showcase to summon on. To select a showcase, use `showcase <showcase>`.
    To get a list of showcases, use `showcase list`.
    To get information about a showcase, use `showcase info <showcase>`
    To select a generic showcase without any rate-up units or dragons, use `showcase none`.

    **Note:** Showcases as represented in the summoning simulator aren't historically accurate. This means:
     - All currently available permanent units are able to be pulled as off-focus units
     - Wyrmprints aren't summonable in the showcases which featured them
     - Showcases which appeared prior to the 5★ dragon rate change on July 31st, 2019 will use the new dragon rates
    """
    args = args.strip()
    if args == "list":
        await message.channel.send(", ".join(sc.name for sc in core.get_summonable_showcase_list()))
    elif args.split(" ")[0].lower() == "info":
        showcase_name = args[5:].strip()
        if not showcase_name:
            showcase_info, showcase = db.get_current_showcase_info(message.channel.id, message.author.id)
            if showcase == core.get_summonable_showcase("none"):
                await message.channel.send(showcase_info)
            else:
                await message.channel.send(showcase_info, embed=showcase.get_embed())
        else:
            showcase = core.get_summonable_showcase(showcase_name)
            if showcase and showcase != core.get_summonable_showcase("none"):
                await message.channel.send(embed=showcase.get_embed())
            else:
                await message.channel.send("I don't know that showcase! Use `showcase list` to see the list of showcases.")
    else:
        showcase = core.get_summonable_showcase(args)
        if showcase:
            await message.channel.send(db.set_showcase(message.channel.id, message.author.id, showcase))
        else:
            await message.channel.send("I don't know that showcase! Use `showcase list` to see the list of showcases.")


async def tenfold_summon(message, args):
    """
    Simulates a tenfold summon on your current showcase.
    To choose a showcase to summon on, use the `showcase` command.
    """
    results, results_text = db.perform_summon(message.channel.id, message.author.id, is_tenfold=True)
    await send_result(message.channel, results, results_text)


async def single_summon(message, args):
    """
    Simulates a single summon on your current showcase.
    To choose a showcase to summon on, use the `showcase` command.
    """
    result, result_text = db.perform_summon(message.channel.id, message.author.id, is_tenfold=False)
    await send_result(message.channel, [result], result_text)


async def send_result(channel, results, message_content):
    if len(results) not in (10, 1):
        raise ValueError("Results must either be a tenfold or a solo")

    if len(results) == 10:
        output_filename = "tenfold.png"
        result_images = [icons.get_entity_icon(e) for e in results]
        output_img_size = (515, 707)
        output_image = Image.new("RGBA", output_img_size)
        result_positions = generate_result_positions(output_img_size)
        for img, pos in zip(result_images, result_positions):
            output_image.paste(img, pos)
    else:
        output_filename = "single.png"
        output_image = icons.get_entity_icon(results[0])

    with io.BytesIO() as fp:
        # profiling results for this function (except sending the message)
        # level     time (s)    size (kb)
        # 6         0.117       255
        # 1         0.050       323
        # 0         0.036       1423
        output_image.save(fp, format="png", compress_level=1)
        fp.seek(0)
        await channel.send(message_content, file=discord.File(fp, filename=output_filename))


def generate_result_positions(canvas_size):
    canvas_w, canvas_h = canvas_size
    row_capacities = [2, 3, 3, 2]
    item_w = 160
    item_h = 160
    item_sep_h = 26
    item_sep_v = 28

    num_cols = max(row_capacities)
    num_rows = len(row_capacities)
    offset_x = (canvas_w - item_w * num_cols - item_sep_h * (num_cols - 1)) // 2 - 1
    offset_y = (canvas_h - item_h * num_rows - item_sep_v * (num_rows - 1)) // 2 - 1

    positions = []
    for y, capacity in enumerate(row_capacities):
        row_offset = (item_w + item_sep_h) * (max(row_capacities) - capacity) // 2
        for x in range(capacity):
            positions.append((
                offset_x + x * (item_w + item_sep_h) + row_offset,
                offset_y + y * (item_h + item_sep_v)
            ))

    return positions


hook.Hook.get("on_init").attach(on_init)
