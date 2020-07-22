import os
import logging
import util
import data
import typing
import aiohttp
import aiofiles
import asyncio
import contextlib
import io
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)


async def update_entity_icons():
    logger.info(f"Updating entity icons")
    os.makedirs(util.path("data/icons"), exist_ok=True)
    required_icons = _get_missing_entity_icons()
    if required_icons:
        logger.info(f"Downloading icons for {len(required_icons)} entities")
        async with aiohttp.ClientSession() as session:
            for file_name in required_icons:
                await _fetch_entity_icon(session, file_name)
                await asyncio.sleep(2)  # don't use too much bandwidth all at once

        logger.info(f"Finished downloading {len(required_icons)} icons")


def _get_missing_entity_icons():
    entities = list(data.Adventurer.get_all()) + list(data.Dragon.get_all())
    icon_info = (f"{e.icon_name}.png" for e in entities)
    return [icon for icon in icon_info if not os.path.exists(util.path(f"data/icons/{icon}"))]


async def _fetch_entity_icon(session: aiohttp.ClientSession, file_name):
    async with session.get(util.get_wiki_cdn_url(file_name)) as response:
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
        # level     time (ms)   size (kB)
        # 6         98          255
        # 1         31          323
        # 0         14          1423
        image.save(fp, format="png", compress_level=1)
        fp.seek(0)
        yield fp


@contextlib.contextmanager
def get_single_image_fp(entity: typing.Union[data.Adventurer, data.Dragon]):
    output_image = Image.new("RGBA", (160, 160))
    paste_entity_image(output_image, entity, (0, 0))

    with _get_image_fp(output_image) as fp:
        yield fp


@contextlib.contextmanager
def get_tenfold_image_fp(results: list):
    output_image_size, result_positions = generate_result_image_constraints((2, 3, 3, 2))
    output_image = Image.new("RGBA", output_image_size)
    for entity, pos in zip(results, result_positions):
        paste_entity_image(output_image, entity, pos)

    with _get_image_fp(output_image) as fp:
        yield fp


def paste_entity_image(output_image, entity, pos):
    if entity.rarity == 5:
        glow_image = {
            data.Adventurer: Image.open(util.path("assets/glow_adventurer.png")),
            data.Dragon: Image.open(util.path("assets/glow_dragon.png")),
        }

        output_image.paste(glow_image[type(entity)], pos)
        output_image.alpha_composite(get_entity_icon(entity), pos)
    else:
        output_image.paste(get_entity_icon(entity), pos)


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
