import hook
import logging
import io
import discord
import util
import contextlib
import sqlite3
from PIL import Image
from . import core, icons

logger = logging.getLogger(__name__)

client = None
current_banner: core.Banner = None
pity_file = util.path("data/pity.db")


async def on_init(discord_client):
    global current_banner, client
    client = discord_client
    current_banner = core.Banner([])

    create_db()

    hook.Hook.get("public!tenfold").attach(tenfold_summon)
    hook.Hook.get("public!single").attach(single_summon)


async def tenfold_summon(message, args):
    """
    Simulates a tenfold summon on a generic banner with no focus units.
    """
    results, pity_progress = perform_summon(current_banner.perform_tenfold, message.channel.id, message.author.id)
    await send_result(message.channel, results, get_pity_explanation_text(current_banner, pity_progress))


async def single_summon(message, args):
    """
    Simulates a single summon on a generic banner with no focus units.
    """
    result, pity_progress = perform_summon(current_banner.perform_solo, message.channel.id, message.author.id)
    await send_result(message.channel, [result], get_pity_explanation_text(current_banner, pity_progress))


def get_pity_explanation_text(banner: core.Banner, pity_progress):
    new_pity = banner.get_five_star_rate(pity_progress)
    summons_left = ((-pity_progress - 1) % 10) + 1
    return f"The 5* rate is now {new_pity}%. {summons_left} summons until the 5* rate increases."


async def send_result(channel, results, message_content):
    if len(results) not in (10, 1):
        raise ValueError("Results must either be a tenfold or a solo")

    if len(results) == 10:
        output_filename = "tenfold.png"
        result_images = [await icons.get_entity_icon(e) for e in results]
        output_img_size = (515, 707)
        output_image = Image.new("RGBA", output_img_size)
        result_positions = generate_result_positions(output_img_size)
        for img, pos in zip(result_images, result_positions):
            output_image.paste(img, pos)
    else:
        output_filename = "single.png"
        output_image = await icons.get_entity_icon(results[0])

    with io.BytesIO() as fp:
        output_image.save(fp, format="png")
        fp.seek(0)
        await channel.send(message_content, file=discord.File(fp, filename=output_filename))


def create_db():
    with contextlib.closing(sqlite3.connect(pity_file)) as connection:
        with connection:
            with contextlib.closing(connection.cursor()) as cursor:
                cursor.execute("CREATE TABLE IF NOT EXISTS pity (channel, user, rate, PRIMARY KEY (channel, user))")


def perform_summon(summon_func, channel_id: int, user_id: int):
    if channel_id and user_id:
        with contextlib.closing(sqlite3.connect(pity_file)) as connection:
            with connection:
                with contextlib.closing(connection.cursor()) as cursor:
                    cursor.execute(
                        "SELECT rate FROM pity WHERE channel = ? AND user = ?",
                        (channel_id, user_id)
                    )
                    result = cursor.fetchone()
                    pity_progress = 0 if result is None else result[0]
                    summon_results, new_pity_progress = summon_func(pity_progress)
                    cursor.execute(
                        "INSERT OR REPLACE INTO pity VALUES (?, ?, ?)",
                        (channel_id, user_id, new_pity_progress)
                    )

                    return summon_results, new_pity_progress
    else:
        raise ValueError(f"Invalid channel id '{channel_id}' or user id '{user_id}'")


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
