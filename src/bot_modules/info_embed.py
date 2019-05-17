import data
import re
import config
import logging
import util
import discord
import io
import jellyfish
import jellyfish._jellyfish as py_jellyfish
import urllib.parse
import hook

logger = logging.getLogger(__name__)

client = None
shortcuts = {}


def edit_distance(a, b):
    try:
        return jellyfish.damerau_levenshtein_distance(a, b)
    except ValueError:
        return py_jellyfish.damerau_levenshtein_distance(a, b)


async def on_init(discord_client):
    global client, shortcuts
    client = discord_client

    logger.info("Resolving query shortcuts")

    shortcut_config = config.get_global_config()["query_shortcuts"]
    entity_maps = {
        "adventurer": data.Adventurer.get_all(),
        "dragon": data.Dragon.get_all(),
        "wyrmprint": data.Wyrmprint.get_all(),
        "skill": data.Skill.get_all()
    }

    for etype in entity_maps:
        emap = entity_maps[etype]
        for short in shortcut_config[etype]:
            expanded = shortcut_config[etype][short]
            try:
                entity = emap[expanded]
            except KeyError:
                logger.warning("Shortcut \"{0}\" = \"{1}\" doesn't resolve to any {2}".format(
                    short,
                    expanded,
                    etype
                ))
                continue

            if short in shortcuts:
                logger.warning("Shortcut {0} resolves multiple times".format(short))
            shortcuts[short] = entity

    logger.info("Query shortcuts resolved.")

    hook.Hook.get("on_message").attach(get_info)
    hook.Hook.get("owner!rawquery").attach(raw_query)


async def raw_query(message, args):
    match_type, match_item, match_distance, match_string = match_entity(args)
    content = repr(match_item)
    if len(content) <= 2048:
        await message.channel.send(
            "Matched {0} (match rating {1})".format(
                str(match_item),
                match_distance
            ),
            embed=discord.Embed(
                title=str(match_item),
                description=repr(match_item)
            )
        )
    else:
        await message.channel.send(
            "Matched {0} (match rating {1})".format(
                str(match_item),
                match_distance
            ),
            file=discord.File(fp=io.BytesIO(bytes(content, "UTF-8")), filename=str(match_item)+".txt")
        )


async def get_info(message):
    if "[[" in message.content:
        matches = re.findall(r"\[\[(.+?)\]\]", message.content.lower())
        if len(matches) > 0:
            query_messages = config.get_global_config()["query_messages"]
            special_query_messages = config.get_global_config()["special_query_messages"]

            if len(matches) > 3:
                await message.channel.send("Too many queries, only the first three will be shown.")

            for match in matches[:3]:
                search_term = match.lower()
                if len(match) > 50:
                    await message.channel.send("That's way too long, I'm not looking for that! " + util.get_emote("notte_stop"))
                    continue

                if search_term in query_messages:
                    await message.channel.send(embed=discord.Embed(
                        title=query_messages[search_term][0],
                        description=query_messages[search_term][1]
                    ))
                    continue

                if search_term in special_query_messages and util.is_special_guild(message.guild):
                    title = special_query_messages[search_term][0]
                    content = special_query_messages[search_term][1]

                    if urllib.parse.urlparse(content).scheme:
                        embed = discord.Embed(title=title)
                        embed.set_image(url=content)
                    else:
                        embed = discord.Embed(title=title, description=content)

                    await message.channel.send(embed=embed)
                    continue

                match_type, match_item, match_distance, match_string = match_entity(search_term)

                if match_type == 2:
                    await message.channel.send(embed=match_item.get_embed())
                elif match_type == 1:
                    if match_string in shortcuts:
                        await message.channel.send(
                            "I'm not sure what \"{0}\" is, did you mean \"{1}\"? "
                            "If so, you can use the shortcut \"{2}\".".format(
                                search_term,
                                str(match_item).lower(),
                                match_string
                            )
                        )
                    else:
                        await message.channel.send("I'm not sure what \"{0}\" is, did you mean \"{1}\"?".format(search_term, match_string))
                else:
                    await message.channel.send("I'm not sure what \"{0}\" is.".format(search_term))


def match_entity(search_string):
    search_locations = [
        shortcuts,
        data.Adventurer.get_all(),
        data.Dragon.get_all(),
        data.Wyrmprint.get_all(),
        data.Skill.get_all(),
        data.Weapon.get_all()
    ]

    match_item = None
    match_distance = 100
    match_string = ""
    for loc in search_locations:
        for key in sorted(loc.keys()):
            d = edit_distance(search_string, key)
            if d < match_distance:
                match_item = loc[key]
                match_distance = d
                match_string = key

    match_threshold = 0.4 + 0.2 * max(len(match_string), len(search_string))

    if match_distance <= match_threshold:
        return 2, match_item, match_distance, match_string
    elif match_distance < match_threshold * 2:
        return 1, match_item, match_distance, match_string
    else:
        return 0, match_item, match_distance, match_string


hook.Hook.get("on_init").attach(on_init)
