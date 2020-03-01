import os
import hook
import logging
import util
import data
import typing
import aiohttp
import aiofiles
import asyncio
import urllib.parse
import json
import itertools
import contextlib
import io
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)
glow_image = {
    data.Adventurer: Image.open(util.path("assets/glow_adventurer.png")),
    data.Dragon: Image.open(util.path("assets/glow_dragon.png")),
}


async def on_init(discord_client):
    os.makedirs(util.path("data/icons"), exist_ok=True)

    hook.Hook.get("download_data_delayed").attach(update_entity_icons)
    hook.Hook.get("owner!update_sim_icons").attach(update_entity_icons_cmd)


async def update_entity_icons_cmd(message, args):
    await update_entity_icons()
    await message.channel.send("Updated summoning sim icons.")


async def update_entity_icons():
    required_icons = _get_missing_entity_icons()
    if required_icons:
        logger.info(f"Downloading icons for {len(required_icons)} entities")
        async with aiohttp.ClientSession() as session:
            icon_urls = await _get_entity_icon_urls(session, required_icons)
            for file_name, url in icon_urls.items():
                await _fetch_entity_icon(session, file_name, url)
                await asyncio.sleep(2)  # don't use too much bandwidth all at once

        logger.info(f"Finished downloading {len(required_icons)} icons")


def _get_missing_entity_icons():
    entities = list(data.Adventurer.get_all().values()) + list(data.Dragon.get_all().values())
    icon_info = (f"{e.icon_name}.png" for e in entities)
    return [icon for icon in icon_info if not os.path.exists(util.path(f"data/icons/{icon}"))]


async def _get_entity_icon_urls(session: aiohttp.ClientSession, icon_names):
    base_url = "https://dragalialost.gamepedia.com/api.php?action=query&prop=imageinfo&iiprop=url&format=json&titles="
    title_chunks = itertools.zip_longest(*([iter(icon_names)] * 50))
    file_urls = {}
    for chunk in title_chunks:
        titles_value = "|".join(f"File:{icon}" for icon in filter(None, chunk))
        url = base_url + urllib.parse.quote(titles_value.replace("_", " "))
        async with session.get(url) as response:
            try:
                response_json = await response.json(content_type=None)
            except json.decoder.JSONDecodeError:
                logger.warning("Could not decode JSON response")
                return None

        results = response_json["query"]["pages"]
        for item in results.values():
            file_name = item["title"].replace(" ", "_")[5:]
            if "missing" in item:
                logger.warning(f"URL requested for non-existent file '{file_name}'")
                continue
            file_urls[file_name] = item["imageinfo"][0]["url"]

    return file_urls


async def _fetch_entity_icon(session: aiohttp.ClientSession, file_name, url):
    async with session.get(url) as response:
        async with aiofiles.open(util.path(f"data/icons/{file_name}"), "wb") as file:
            await file.write(await response.read())


def get_entity_icon(entity: typing.Union[data.Adventurer, data.Dragon]):
    icon_path = util.path(f"data/icons/{entity.icon_name}.png")
    try:
        return Image.open(icon_path)
    except (FileNotFoundError, UnidentifiedImageError) as e:
        if type(e) == UnidentifiedImageError:
            os.remove(icon_path)
            logger.warning(f"Bad image file {entity.icon_name}.png removed for reacquisition")

        if isinstance(entity, data.Adventurer):
            return Image.open(util.path("assets/frame_adventurer.png"))
        elif isinstance(entity, data.Dragon):
            return Image.open(util.path("assets/frame_dragon.png"))
        else:
            raise ValueError(f"Unexpected entity type {type(entity)}")


@contextlib.contextmanager
def _get_image_fp(image):
    with io.BytesIO() as fp:
        # profiling results for encoding tenfold png
        # level     time (s)    size (kb)
        # 6         0.098       255
        # 1         0.031       323
        # 0         0.014       1423
        image.save(fp, format="png", compress_level=1)
        fp.seek(0)
        yield fp


@contextlib.contextmanager
def get_single_image_fp(entity: typing.Union[data.Adventurer, data.Dragon]):
    if entity.rarity == 5:
        output_image = Image.new("RGBA", (160, 160))
        output_image.paste(glow_image[type(entity)])
        output_image.alpha_composite(get_entity_icon(entity))
    else:
        output_image = get_entity_icon(entity)

    with _get_image_fp(output_image) as fp:
        yield fp


@contextlib.contextmanager
def get_tenfold_image_fp(results: list):
    output_image_size, result_positions = generate_result_image_constraints((2, 3, 3, 2))
    output_image = Image.new("RGBA", output_image_size)
    for entity, pos in zip(results, result_positions):
        if entity.rarity == 5:
            output_image.paste(glow_image[type(entity)], pos)
            output_image.alpha_composite(get_entity_icon(entity), pos)
        else:
            output_image.paste(get_entity_icon(entity), pos)

    with _get_image_fp(output_image) as fp:
        yield fp


def generate_result_image_constraints(row_capacities):
    margin = (0, 0)
    offset = (0, 0)
    item_size = (160, 160)
    item_sep = (26, 28)
    max_cols = max(row_capacities)
    num_rows = len(row_capacities)
    canvas_w = item_size[0] * max_cols + item_sep[0] * (max_cols - 1) + margin[0]
    canvas_h = item_size[1] * num_rows + item_sep[1] * (num_rows - 1) + margin[1]

    positions = []
    for y, capacity in enumerate(row_capacities):
        row_offset = (item_size[0] + item_sep[0]) * (max(row_capacities) - capacity) // 2
        for x in range(capacity):
            positions.append((
                offset[0] + x * (item_size[0] + item_sep[0]) + row_offset,
                offset[1] + y * (item_size[1] + item_sep[1])
            ))

    return (canvas_w, canvas_h), positions


hook.Hook.get("on_init").attach(on_init)
