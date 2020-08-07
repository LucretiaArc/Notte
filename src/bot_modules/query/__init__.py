import re
import discord
import urllib.parse
import hook
import logging
import config
import time
from . import queries
from fuzzy_match import Matcher

logger = logging.getLogger(__name__)

matcher: Matcher = None
query_config = None


async def on_init(discord_client):
    global query_config
    query_config = config.get_global("custom_query")

    build_matcher()

    hook.Hook.get("on_message").attach(scan_for_query)
    hook.Hook.get("data_downloaded").attach(build_matcher)


async def scan_for_query(message):
    if "[" in message.content:
        matches = re.findall(r"\[\[(.+?)\]\]", message.content.lower())
        if len(matches) > 0:
            if len(matches) > 3:
                await message.channel.send("Too many queries, only the first three will be shown.")

            is_special_guild = message.guild and message.guild.id in query_config["special_guilds"]
            for raw_match in matches[:3]:
                if len(raw_match) > matcher.max_query_len + 5:
                    await message.channel.send("That's way too much, I'm not looking for that!")
                    continue

                response = resolve_query(raw_match, is_special_guild)
                if isinstance(response, discord.Embed):
                    await message.channel.send(embed=response)
                else:
                    await message.channel.send(response)


def resolve_query(query: str, include_special_responses=False):
    special_query_messages = query_config["special_query_messages"]
    regular_query_messages = query_config["query_messages"]
    search_term = query.lower()
    embed = None

    # resolve custom query messages
    custom_query = None
    if search_term in special_query_messages and include_special_responses:
        custom_query = special_query_messages[search_term]
    elif search_term in regular_query_messages:
        custom_query = regular_query_messages[search_term]

    if custom_query:
        title, content = custom_query
        if urllib.parse.urlparse(content).scheme:
            embed = discord.Embed(title=title).set_image(url=content)
        else:
            embed = discord.Embed(title=title, description=content)
    else:
        match_content = matcher.match(search_term)
        if match_content:
            match_obj = match_content[0]
            if isinstance(match_obj, discord.embeds.Embed):
                embed = match_obj.copy()
            else:
                embed = match_obj.get_embed().copy()

            if match_content[2] < 1:
                embed.set_footer(text=f'Displaying result for "{match_content[1]}"')

    return embed or f"I'm not sure what \"{query}\" is."


def build_matcher():
    global matcher
    logger.info("Generating queries...")
    start_time = time.perf_counter()
    new_matcher = Matcher()
    queries.create_queries(new_matcher)
    matcher = new_matcher
    logger.info(f"{len(matcher.match_map)} queries generated in {time.perf_counter() - start_time:.1f} seconds")
    logger.info(f"Determined maximum query length {matcher.max_query_len}")


hook.Hook.get("on_init").attach(on_init)
