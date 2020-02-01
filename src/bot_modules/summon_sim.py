import hook
import logging
import data
import typing
import random
import aiohttp
import json
import os
import itertools
import urllib.parse
import asyncio
import io
import discord
from PIL import Image

logger = logging.getLogger(__name__)

client = None
current_banner: "Banner" = None


async def on_init(discord_client):
    global client, current_banner
    client = discord_client
    current_banner = Banner([])

    hook.Hook.get("public!tenfold").attach(tenfold_summon)
    hook.Hook.get("public!single").attach(single_summon)
    hook.Hook.get("download_data_delayed").attach(update_entity_icons)
    hook.Hook.get("owner!update_sim_icons").attach(update_entity_icons_cmd)


async def tenfold_summon(message, args):
    """
    Simulates a tenfold summon.
    """
    results = current_banner.perform_tenfold(0, 0)[0]
    result_images = [await get_entity_icon(e) for e in results]
    output_img_size = (515, 707)
    output_image = Image.new("RGBA", output_img_size)
    result_positions = generate_result_positions(output_img_size)
    for img, pos in zip(result_images, result_positions):
        output_image.paste(img, pos)

    fp = io.BytesIO()
    output_image.save(fp, format="png")
    fp.seek(0)
    await message.channel.send(file=discord.File(fp, filename="tenfold.png"))


async def single_summon(message, args):
    """
    Simulates a single summon.
    """
    result = current_banner.perform_solo(0, 0)[0]
    output_image = await get_entity_icon(result)

    fp = io.BytesIO()
    output_image.save(fp, format="png")
    fp.seek(0)
    await message.channel.send(file=discord.File(fp, filename="single.png"))


async def update_entity_icons_cmd(message, args):
    await update_entity_icons()
    await message.channel.send("Updated summoning sim icons.")


class Banner:
    def __init__(self, featured: typing.List[typing.Union[data.Adventurer, data.Dragon]]):
        self.is_gala = any(e.availability == "Gala" for e in featured)
        self.entity_pools = {r: {f: {t: [] for t in (data.Adventurer, data.Dragon)} for f in ("f", "n")} for r in range(3, 6)}

        for e in featured:
            if e.rarity:
                self.entity_pools[e.rarity]["f"][type(e)].append(e)

        normal_pool = (set(data.Adventurer.get_all().values()) | set(data.Dragon.get_all().values())) - set(featured)
        for e in normal_pool:
            if e.rarity and (e.availability == "Permanent" or (self.is_gala and e.availability == "Gala")):
                self.entity_pools[e.rarity]["n"][type(e)].append(e)

    def get_pool_rates(self, pity):
        rates = {r: {f: {t: 0 for t in (data.Adventurer, data.Dragon)} for f in ("f", "n")} for r in range(3, 6)}

        # 5* rates
        base_5_rate = 6 if self.is_gala else 4
        total_5_rate = base_5_rate + pity
        rate_multi_5 = total_5_rate / base_5_rate
        featured_5_adv_count = len(self.entity_pools[5]["f"][data.Adventurer])
        featured_5_drg_count = len(self.entity_pools[5]["f"][data.Dragon])
        rates[5]["f"][data.Adventurer] = rate_multi_5 * 0.5 * featured_5_adv_count
        rates[5]["f"][data.Dragon] = rate_multi_5 * 0.8 * featured_5_drg_count
        rates[5]["n"][data.Adventurer] = total_5_rate / 2 - rates[5]["f"][data.Adventurer]
        rates[5]["n"][data.Dragon] = total_5_rate / 2 - rates[5]["f"][data.Dragon]

        # 4* rates
        featured_4_adv_count = len(self.entity_pools[4]["f"][data.Adventurer])
        featured_4_drg_count = len(self.entity_pools[4]["f"][data.Dragon])
        featured_4_total_count = featured_4_adv_count + featured_4_drg_count
        if featured_4_total_count:
            rates[4]["f"][data.Adventurer] = 7 * featured_4_adv_count / featured_4_total_count
            rates[4]["f"][data.Dragon] = 7 * featured_4_drg_count / featured_4_total_count
            rates[4]["n"][data.Adventurer] = 5.05
            rates[4]["n"][data.Dragon] = 3.95
        else:
            rates[4]["n"][data.Adventurer] = 8.55
            rates[4]["n"][data.Dragon] = 7.45

        # 3* rates
        normal_3_rate_split = 80 - pity
        offset_3_rate = -1 if self.is_gala else 0
        featured_3_adv_count = len(self.entity_pools[3]["f"][data.Adventurer])
        featured_3_drg_count = len(self.entity_pools[3]["f"][data.Dragon])
        rates[3]["f"][data.Adventurer] = 4 * featured_3_adv_count
        rates[3]["f"][data.Dragon] = 4 * featured_3_drg_count
        rates[3]["n"][data.Adventurer] = 0.6 * normal_3_rate_split - rates[3]["f"][data.Adventurer] + offset_3_rate
        rates[3]["n"][data.Dragon] = 0.4 * normal_3_rate_split - rates[3]["f"][data.Dragon] + offset_3_rate

        return rates

    def is_pity_rate_capped(self, pity):
        return pity >= (3 if self.is_gala else 5)

    def _get_result(self, rates):
        weights = []
        pools = []
        for rarity, rarity_pool in self.entity_pools.items():
            for is_featured, sub_pool in rarity_pool.items():
                for e_type, type_pool in sub_pool.items():
                    pools.append(type_pool)
                    weights.append(rates[rarity][is_featured][e_type])

        selected_pool = random.choices(pools, weights=weights)[0]
        return random.choice(selected_pool)

    def perform_solo(self, pity, pity_progress):
        rates = self.get_pool_rates(pity)
        adjust_rates(rates, guaranteed_5=self.is_pity_rate_capped(pity))
        result = self._get_result(rates)
        if result.rarity == 5:
            pity = 0
            pity_progress = 0
        else:
            pity, pity_progress = increment_pity_progress(pity, pity_progress, 1)
        return result, pity, pity_progress

    def perform_tenfold(self, pity, pity_progress):
        rates = self.get_pool_rates(pity)
        results = [self._get_result(rates) for i in range(9)]
        received_5 = any(e.rarity == 5 for e in results)
        adjust_rates(rates, guaranteed_5=self.is_pity_rate_capped(pity), guaranteed_4=True)
        results.append(self._get_result(rates))
        if received_5 or results[-1].rarity == 5:
            pity = 0
            pity_progress = 0
        else:
            pity, pity_progress = increment_pity_progress(pity, pity_progress, 10)
        return results, pity, pity_progress


def adjust_rates(rates, guaranteed_5=False, guaranteed_4=False):
    if guaranteed_5:
        set_rarity_rate(rates[3], 0)
        set_rarity_rate(rates[4], 0)
        set_rarity_rate(rates[5], 100)
    elif guaranteed_4:
        old_3_rate = set_rarity_rate(rates[3], 0)
        set_rarity_rate(rates[4], 16 + old_3_rate)


def set_rarity_rate(rarity_rates, new_rate):
    old_rate = sum(rarity_rates["f"].values()) + sum(rarity_rates["n"].values())
    rate_scale = new_rate / old_rate
    for is_featured, type_pool in rarity_rates.items():
        for e_type in type_pool:
            type_pool[e_type] *= rate_scale

    return old_rate


def increment_pity_progress(pity, pity_progress, increment_amount):
    pity_progress += increment_amount
    pity += 0.5 * (pity_progress // 10)
    pity_progress %= 10
    return pity, pity_progress


async def update_entity_icons():
    required_icons = check_entity_icons()
    if required_icons:
        logger.info(f"Downloading icons for {len(required_icons)} entities")
        async with aiohttp.ClientSession() as session:
            icon_urls = await get_entity_icon_urls(session, required_icons)
            for file_name, url in icon_urls.items():
                await fetch_entity_icon(session, file_name, url)
                await asyncio.sleep(10)  # don't use too much bandwidth all at once

        logger.info(f"Finished downloading {len(required_icons)} icons")


def check_entity_icons():
    entities = list(data.Adventurer.get_all().values()) + list(data.Dragon.get_all().values())
    icon_info = (f"{e.icon_name}.png" for e in entities)
    return [icon for icon in icon_info if not os.path.exists(f"../data/{icon}")]


async def get_entity_icon_urls(session: aiohttp.ClientSession, icon_names):
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


async def fetch_entity_icon(session: aiohttp.ClientSession, file_name, url):
    async with session.get(url) as response:
        with open(f"../data/{file_name}", "wb") as file:
            file.write(await response.read())


async def get_entity_icon(entity):
    try:
        icon_image = Image.open(f"../data/{entity.icon_name}.png")
    except FileNotFoundError:
        if isinstance(entity, data.Adventurer):
            icon_image = Image.open("../upload/frame_adventurer.png")
        elif isinstance(entity, data.Dragon):
            icon_image = Image.open("../upload/frame_dragon.png")
        else:
            raise ValueError(f"Unexpected entity type {type(entity)}")

    return icon_image


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
