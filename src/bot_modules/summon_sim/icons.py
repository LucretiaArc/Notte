import os
import hook
import logging
import util
import data
import aiohttp
import aiofiles
import asyncio
import urllib.parse
import json
import itertools
from PIL import Image

logger = logging.getLogger(__name__)


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
                await asyncio.sleep(10)  # don't use too much bandwidth all at once

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
            file.write(await response.read())


def get_entity_icon(entity):
    try:
        icon_image = Image.open(util.path(f"data/icons/{entity.icon_name}.png"))
    except FileNotFoundError:
        if isinstance(entity, data.Adventurer):
            icon_image = Image.open(util.path("assets/frame_adventurer.png"))
        elif isinstance(entity, data.Dragon):
            icon_image = Image.open(util.path("assets/frame_dragon.png"))
        else:
            raise ValueError(f"Unexpected entity type {type(entity)}")

    return icon_image


hook.Hook.get("on_init").attach(on_init)
