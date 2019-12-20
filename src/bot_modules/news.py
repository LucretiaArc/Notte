import datetime
import asyncio
import config
import aiohttp
import logging
import json
import util
import discord
import html.parser
import re
import math
import hook

logger = logging.getLogger(__name__)

client = None
news_icon = "https://cdn.discordapp.com/attachments/560454966154756107/599274542732410890/news.png"


def get_news_colour(is_update=False): return 0xFF6600 if is_update else 0x00A0FF


async def on_init(discord_client):
    global client
    client = discord_client

    now = datetime.datetime.utcnow()
    mins_past_hour = (now - now.replace(minute=0, second=0, microsecond=0)).total_seconds() / 60
    seconds_wait = 60 * (5 - (mins_past_hour - 5 * math.floor(mins_past_hour / 5))) + 5
    asyncio.get_event_loop().call_later(seconds_wait, lambda: asyncio.ensure_future(check_news(True)))

    if seconds_wait > 30:
        await check_news(False)

    hook.Hook.get("owner!check_news").attach(lambda m, a: asyncio.ensure_future(check_news(False)))
    hook.Hook.get("on_reset").attach(lambda: asyncio.ensure_future(check_news(False)))


async def check_news(reschedule):
    if reschedule:
        # trigger next 5 minute interval (5 secs delayed)
        now = datetime.datetime.utcnow()
        time_delta = (now + datetime.timedelta(5 / 1440)).replace(second=5, microsecond=0) - now
        asyncio.get_event_loop().call_later(time_delta.total_seconds(), lambda: asyncio.ensure_future(check_news(True)))

    async with aiohttp.ClientSession() as session:
        list_base_url = "https://dragalialost.com/api/index.php?" \
                        "format=json&type=information&action=information_list&lang=en_us&priority_lower_than="

        wc = config.get_writeable()
        stored_recent_article_ids = wc.news_recent_article_ids
        stored_recent_article_date = wc.news_recent_article_date

        if not stored_recent_article_ids or not stored_recent_article_date:
            logger.warning("Missing article history, regenerating...")
            stored_recent_article_ids = []
            stored_recent_article_date = 0
            regenerate_config = True
        else:
            regenerate_config = False

        new_recent_article_ids = stored_recent_article_ids.copy()
        new_recent_article_date = stored_recent_article_date
        news_items = []
        news_item_ids = set()
        next_priority = 1e9
        found_new_items = True
        while found_new_items:
            response_json = await get_api_json_response(session, list_base_url + str(next_priority))
            if not response_json:
                logger.warning("Could not retrieve article list")
                return

            query_result = response_json["data"]["category"]

            found_new_items = False
            for item in query_result["contents"]:
                article_id = item["article_id"]
                article_date = get_article_date(item)

                # remember date of most recent article, along with all articles posted at that time
                if article_date > new_recent_article_date:
                    new_recent_article_date = article_date
                    new_recent_article_ids = [article_id]
                    if regenerate_config:
                        stored_recent_article_date = new_recent_article_date
                elif article_date == new_recent_article_date and article_id not in new_recent_article_ids:
                    new_recent_article_ids.append(article_id)

                # determine whether to post this article
                if (article_date > stored_recent_article_date) or (
                        article_date == stored_recent_article_date and article_id not in stored_recent_article_ids):
                    found_new_items = True
                    if article_id not in news_item_ids:
                        news_items.append(item)
                        news_item_ids.add(article_id)

            next_priority = util.safe_int(query_result["priority_lower_than"], 0)

        if regenerate_config:
            wc.news_recent_article_ids = new_recent_article_ids
            wc.news_recent_article_date = new_recent_article_date
            logger.warning(f"Regenerated, recent article date = {new_recent_article_date}, IDs = {new_recent_article_ids}")
            config.set_writeable(wc)
            return

        # sort news items for correct order
        news_items = sorted(news_items, key=lambda d: d["priority"])

        if len(news_items) >= 10:
            # too many news items, post a generic notification
            embeds = [discord.Embed(
                title="New news posts are available",
                url="https://dragalialost.com/en/news/",
                description=f"{len(news_items)} new news posts are available! Click the link above to read them.",
                color=get_news_colour()
            ).set_author(
                name="Dragalia Lost News",
                icon_url=news_icon
            )]
        else:
            # generate embeds from articles
            embeds = []
            article_blacklist = config.get_global("general")["news_article_blacklist"]
            for item in news_items:
                if item["article_id"] not in article_blacklist:
                    item_embed = await get_embed_from_result(session, item)
                    if item_embed:
                        embeds.append(item_embed)

        # update config
        if len(news_items):
            wc.news_recent_article_ids = new_recent_article_ids
            wc.news_recent_article_date = new_recent_article_date
            config.set_writeable(wc)

        # post news items
        for guild in client.guilds:
            active_channel = config.get_guild(guild).active_channel
            channel = guild.get_channel(active_channel)
            if channel is not None and channel.permissions_for(guild.me).send_messages:
                asyncio.ensure_future(exec_in_order([channel.send(embed=e) for e in embeds]))


async def get_embed_from_result(session: aiohttp.ClientSession, item: dict):
    article_id = item["article_id"]
    article_url = f"https://dragalialost.com/en/news/detail/{article_id}"
    article_title = item["title_name"]
    article_date = datetime.datetime.utcfromtimestamp(get_article_date(item))
    article_category = item["category_name"]
    article_is_update = item["is_update"]

    logger.info(f"Retrieving news content for article {article_id}")
    content_url = f"https://dragalialost.com/api/index.php" \
        f"?format=json&type=information&action=information_detail&lang=en_us&article_id={article_id}"

    article_json = await get_api_json_response(session, content_url)
    if not article_json:
        logger.warning("Could not retrieve article content")
        return None

    html_content = get_html_content(article_json)

    article_content_sections = html_content.split("\n")
    if "Dragalia Life" in article_title and "Now Available" in article_title:
        comic_number_match = re.search(r"#(\d+)", article_title)
        if comic_number_match:
            comic_number = int(comic_number_match.group(1))
            embed = await get_comic_embed(session, comic_number, article_is_update)
        else:
            embed = get_news_embed(article_title, article_url, article_content_sections, article_is_update)
    elif article_title in ("Astral Raids Are Here!", "Astral Raids Are Starting Soon!"):
        embed = get_astral_raids_embed(article_title, article_url, article_content_sections, article_is_update)
    else:
        embed = get_news_embed(article_title, article_url, article_content_sections, article_is_update)

    article_date_pretty = article_date.strftime("%B %d, %I:%M %p (UTC)")
    embed.set_author(
        name=f"{article_category} | Dragalia Lost News",
        icon_url=news_icon
    ).set_footer(
        text=f"{'Updated' if article_is_update else 'Posted'} {article_date_pretty}"
    )

    logger.info(f"Retrieved article {article_id} posted {article_date_pretty}")
    return embed


async def get_comic_embed(session: aiohttp.ClientSession, comic_number: int, is_update):
    request_data = {"lang": "en", "type": "dragalialife"}
    api_base_url = "https://comic.dragalialost.com/api/thumbnail_list/"
    comic_base_url = "https://comic.dragalialost.com/dragalialife/en/#detail/"
    page_id = 0
    page_size = 20
    comic_data = {}
    attempts = 0
    # most of the time, the comic is going to be on page 0. In other cases, we'd still like to get the comic info.
    # we don't use caching, as we're expecting to need to pull new data for almost every call.
    while attempts < 2 and not comic_data:
        async with session.post(api_base_url + str(page_id), data=request_data) as response:
            comic_list = await response.json(content_type=None)
            comic_data = next(filter(lambda c: int(c["episode_num"]) == comic_number, comic_list), None)
            page_id = math.ceil(int(comic_list[0]["episode_num"]) / page_size) - math.ceil(comic_number / page_size)
            if page_id <= 0:
                break
            else:
                attempts += 1

    if not comic_data:
        return None

    comic_title = comic_data["title"]
    comic_url = comic_base_url + comic_data["id"]
    comic_thumbnail_url = comic_data["thumbnail_s"]
    title = f"Dragalia Life #{comic_number}, Now Available!"
    content = f"Issue #{comic_number} of the comic strip Dragalia Life, \"{comic_title}\", is now available! " \
        "Click on the link above to view it."

    return discord.Embed(
        title=title,
        url=comic_url,
        description=content,
        color=get_news_colour(is_update)
    ).set_thumbnail(
        url=comic_thumbnail_url
    )


def get_astral_raids_embed(article_title, article_url, article_content_sections, is_update):
    content = article_content_sections[0]
    raid_boss = article_content_sections[article_content_sections.index("\u25a0Featured Boss")+1]
    return discord.Embed(
        title=f"{article_title} ({raid_boss})",
        url=article_url,
        description=content,
        color=get_news_colour(is_update)
    )


def get_news_embed(article_title, article_url, content_sections, is_update):
    content = ""
    section_count = 0
    for p in content_sections:
        content += "\n" + p
        section_count += 1
        if len(content) > 100:
            break
    content = re.sub("\n{3,}", "\n\n", content).strip()
    if section_count < len(content_sections):
        content += "\n\n...\n\u200b"

    return discord.Embed(
        title=article_title,
        url=article_url,
        description=content,
        color=get_news_colour(is_update)
    )


async def get_api_json_response(session: aiohttp.ClientSession, url: str):
    async with session.get(url) as response:
        try:
            response_json = await response.json(content_type=None)
        except json.decoder.JSONDecodeError:
            logger.warning("Could not decode JSON response")
            return None

        if response_json["data_headers"]["result_code"] != 1:
            logger.error("Error performing query, data_headers = " + json.dumps(response_json["data_headers"]))
            return None

        return response_json


def get_html_content(article_json):
    html_content = article_json["data"]["information"]["message"]
    html_content = html_content.replace("</div>", "\n")
    html_content = html_content.replace("<br>", "\n")
    html_content = re.sub(
        r'<span[^>]+data-local_date="([\d]+)[^>]+>',
        lambda m: datetime.datetime.utcfromtimestamp(int(m.group(1))).strftime("%I:%M %p, %b %d, %Y (UTC)"),
        html_content
    )

    t = TagStripper()
    t.feed(html_content)
    return t.get_data()


def get_article_date(item: dict):
    if item["is_update"]:
        return max(item["date"], item["update_time"])
    else:
        return item["date"]


async def exec_in_order(coroutines):
    for c in coroutines:
        await c


class TagStripper(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


hook.Hook.get("on_init").attach(on_init)
