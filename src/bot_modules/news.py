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
from hook import Hook

logger = logging.getLogger(__name__)

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    await check_news()


async def check_news():
    # trigger next 5 minute interval (15 secs delayed)
    now = datetime.datetime.utcnow()
    time_delta = (now + datetime.timedelta(5 / 1440)).replace(second=15, microsecond=0) - now
    asyncio.get_event_loop().call_later(time_delta.total_seconds(), lambda: asyncio.ensure_future(check_news()))

    logger.info("Collecting news info")
    async with aiohttp.ClientSession() as session:
        list_base_url = "https://dragalialost.com/api/index.php?" \
                        "format=json&type=information&action=information_list&lang=en_us&priority_lower_than="
        content_base_url = "https://dragalialost.com/api/index.php?" \
                           "format=json&type=information&action=information_detail&lang=en_us&article_id="

        wconfig = config.get_wglobal_config()
        last_priority = wconfig.get("news_last_priority")
        next_priority = 1e9
        max_priority = None
        news_items = []
        while True:
            async with session.get(list_base_url + str(next_priority)) as response:
                result_json = await response.json(content_type=None)

                if result_json["data_headers"]["result_code"] != 1:
                    logger.error("Error retrieving news list: data_headers = " + json.dumps(result_json["data_headers"]))
                    return

                query_result = result_json["data"]["category"]

                news_items += query_result["contents"]
                next_priority = util.safe_int(query_result["priority_lower_than"], 0)

                if not query_result["more_posts"] or next_priority-1 <= last_priority:
                    break

        embeds = []

        for item in news_items:
            if util.safe_int(item["priority"], 0) <= last_priority:
                break

            max_priority = max_priority or int(item["priority"])

            title = item["title_name"]
            date = datetime.datetime.utcfromtimestamp(item["date"])
            article_url = "https://dragalialost.com/en/news/detail/" + str(item["article_id"])
            category = item["category_name"]
            content = ""

            async with session.get(content_base_url + str(item["article_id"])) as response:
                result_json = await response.json(content_type=None)

                if result_json["data_headers"]["result_code"] != 1:
                    logger.error("Error retrieving news content for article " + str(item["article_id"]))
                    content = None
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
                        content = sections[0]
                    else:
                        section_count = 0
                        for p in sections:
                            content += "\n" + p
                            section_count += 1
                            if len(content) > 100:
                                break
                        content = re.sub("\n+", "\n\n", content).strip()
                        if section_count < len(sections):
                            content += "\n\n...\n\u200b"

            e = discord.Embed(
                title=title,
                url=article_url,
                description=content,
                color=0x00A0FF
            )
            e.set_author(
                name=category+" | Dragalia Lost News",
                icon_url="https://dragalialost.com/assets/en/images/pc/top/kv_logo.png"
            )
            e.set_footer(text="Posted " + date.strftime("%B %d, %I:%M %p (UTC)"))
            embeds.append(e)

        for guild in client.guilds:
            active_channel = config.get_guild_config(guild)["active_channel"]
            channel = guild.get_channel(active_channel)
            if channel is not None and channel.permissions_for(guild.me).send_messages:
                for e in embeds:
                    await channel.send(embed=e)

        if max_priority:
            wconfig["news_last_priority"] = max_priority
            config.set_wglobal_config(wconfig)


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


Hook.get("on_init").attach(on_init)
