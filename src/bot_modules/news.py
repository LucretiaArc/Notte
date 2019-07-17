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
news_colour = 0x00A0FF


async def on_init(discord_client):
    global client
    client = discord_client

    now = datetime.datetime.utcnow()
    mins_past_hour = (now - now.replace(minute=0, second=0, microsecond=0)).total_seconds() / 60
    seconds_wait = 60*(5 - (mins_past_hour - 5*math.floor(mins_past_hour/5))) + 15
    asyncio.get_event_loop().call_later(seconds_wait, lambda: asyncio.ensure_future(check_news(True)))

    if seconds_wait > 30:
        await check_news(False)


async def check_news(reschedule):
    if reschedule:
        # trigger next 5 minute interval (15 secs delayed)
        now = datetime.datetime.utcnow()
        time_delta = (now + datetime.timedelta(5 / 1440)).replace(second=15, microsecond=0) - now
        asyncio.get_event_loop().call_later(time_delta.total_seconds(), lambda: asyncio.ensure_future(check_news(True)))

    async with aiohttp.ClientSession() as session:
        list_base_url = "https://dragalialost.com/api/index.php?" \
                        "format=json&type=information&action=information_list&lang=en_us&priority_lower_than="
        content_base_url = "https://dragalialost.com/api/index.php?" \
                           "format=json&type=information&action=information_detail&lang=en_us&article_id="

        wconfig = config.get_wglobal_config()
        last_article_id = wconfig.get("news_last_article_id")
        last_article_date = wconfig.get("news_last_article_date")

        next_priority = 1e9
        news_items = []
        found_all_items = False
        while not found_all_items:
            async with session.get(list_base_url + str(next_priority)) as response:
                try:
                    result_json = await response.json(content_type=None)
                except json.decoder.JSONDecodeError:
                    logger.warning("Could not decode news: malformed response")
                    return

                if result_json["data_headers"]["result_code"] != 1:
                    # invalid query
                    logger.error("Error retrieving news list: data_headers = " + json.dumps(result_json["data_headers"]))
                    return

                query_result = result_json["data"]["category"]

                if last_article_id == 0 or last_article_date == 0:
                    # default config
                    logger.warning("Setting last news article id and date to match recent article")
                    recent_article = query_result["contents"][0]
                    wconfig["news_last_article_id"] = recent_article["article_id"]
                    wconfig["news_last_article_date"] = recent_article["date"]
                    config.set_wglobal_config(wconfig)
                    return

                for item in query_result["contents"]:
                    if item["article_id"] == last_article_id or item["date"] < last_article_date:
                        found_all_items = True
                        break
                    else:
                        news_items.append(item)

                next_priority = util.safe_int(query_result["priority_lower_than"], 0)

        # sort news items for correct order
        news_items = sorted(news_items, key=lambda d: d["priority"])

        if len(news_items) > 10:
            embeds = [discord.Embed(
                title="New news posts are available",
                url="https://dragalialost.com/en/news/",
                description=f"{len(news_items)} new news posts are available! Click the link above to read them.",
                color=news_colour
            ).set_author(
                name="Dragalia Lost News",
                icon_url=news_icon
            )]
        else:
            embeds = []
            for item in news_items:
                title = item["title_name"]
                date = datetime.datetime.utcfromtimestamp(item["date"])
                article_url = "https://dragalialost.com/en/news/detail/" + str(item["article_id"])
                category = item["category_name"]
                embed = None

                logger.info("Retrieving news content for article " + str(item["article_id"]))
                async with session.get(content_base_url + str(item["article_id"])) as response:
                    result_json = await response.json(content_type=None)

                    if result_json["data_headers"]["result_code"] != 1:
                        logger.error("Error retrieving news content for article " + str(item["article_id"]))
                    else:
                        html_content = result_json["data"]["information"]["message"]
                        html_content = html_content.replace("</div>", "\n")
                        html_content = html_content.replace("<br>", "\n")
                        html_content = re.sub(
                            r'<span[^>]+data-local_date="([\d]+)[^>]+>',
                            lambda m: datetime.datetime.utcfromtimestamp(int(m.group(1))).strftime("%I:%M %p, %b %d, %Y (UTC)"),
                            html_content
                        )

                        t = TagStripper()
                        t.feed(html_content)
                        html_content = t.get_data()

                        sections = html_content.split("\n")

                        if "Dragalia Life" in title and "Now Available" in title:
                            comic_number_match = re.search(r"#(\d+)", title)
                            if comic_number_match:
                                comic_number = int(comic_number_match.group(1))
                                embed = await get_comic_embed(session, comic_number)
                            else:
                                embed = await get_news_embed(title, article_url, sections)
                        else:
                            embed = await get_news_embed(title, article_url, sections)

                if embed:
                    embed.set_author(
                        name=category+" | Dragalia Lost News",
                        icon_url=news_icon
                    ).set_footer(
                        text="Posted " + date.strftime("%B %d, %I:%M %p (UTC)")
                    )
                    embeds.append(embed)
                    logger.info("Posting article with timestamp {0} and id {1}".format(item["date"], item["article_id"]))

        if len(news_items):
            wconfig["news_last_article_id"] = news_items[-1]["article_id"]
            wconfig["news_last_article_date"] = news_items[-1]["date"]
            config.set_wglobal_config(wconfig)

        for guild in client.guilds:
            active_channel = config.get_guild_config(guild)["active_channel"]
            channel = guild.get_channel(active_channel)
            if channel is not None and channel.permissions_for(guild.me).send_messages:
                for e in embeds:
                    await channel.send(embed=e)


async def get_comic_embed(session: aiohttp.ClientSession, comic_number: int):
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
            print(comic_number, page_id)
            comic_list = await response.json(content_type=None)
            comic_data = next(filter(lambda c: int(c["episode_num"]) == comic_number, comic_list), None)
            page_id = math.ceil(int(comic_list[0]["episode_num"])/page_size) - math.ceil(comic_number/page_size)
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
        color=news_colour
    ).set_thumbnail(
        url=comic_thumbnail_url
    )


async def get_news_embed(article_title, article_url, content_sections):
    content = ""
    section_count = 0
    for p in content_sections:
        content += "\n" + p
        section_count += 1
        if len(content) > 100:
            break
    content = re.sub("\n+", "\n\n", content).strip()
    if section_count < len(content_sections):
        content += "\n\n...\n\u200b"

    return discord.Embed(
        title=article_title,
        url=article_url,
        description=content,
        color=news_colour
    )


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
