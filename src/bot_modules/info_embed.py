import data
import re
import config
import logging
import util
import discord
import jellyfish
import jellyfish._jellyfish as py_jellyfish
from hook import Hook

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
        "adventurer": data.Adventurer.adventurers,
        "dragon": data.Dragon.dragons,
        "wyrmprint": data.Wyrmprint.wyrmprints
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

    Hook.get("on_message").attach(get_info)


async def get_info(message):
    if "[[" in message.content:
        matches = re.findall(r"\[\[(.+?)\]\]", message.content.lower())
        if len(matches) > 0:
            query_messages = config.get_global_config()["query_messages"]
            special_query_messages = config.get_global_config()["special_query_messages"]
            search_locations = [
                shortcuts,
                data.Adventurer.adventurers,
                data.Dragon.dragons,
                data.Wyrmprint.wyrmprints,
                data.Skill.skills
            ]

            if len(matches) > 3:
                await message.channel.send("Too many queries, only the first three will be shown.")

            for match in matches[:3]:
                search_term = match.lower()
                if len(match) > 30:
                    await message.channel.send("That's way too long, I'm not looking for that! " + util.get_emote("notte_stop"))
                    continue

                if search_term in query_messages:
                    await message.channel.send(embed=discord.Embed(
                        title=query_messages[search_term][0],
                        description=query_messages[search_term][1]
                    ))
                    continue

                if search_term in special_query_messages and util.is_special_guild(message.guild):
                    await message.channel.send(embed=discord.Embed(
                        title=special_query_messages[search_term][0],
                        description=special_query_messages[search_term][1]
                    ))
                    continue

                best_match = (None, 100, "")  # (matching item, match distance, match string)
                for loc in search_locations:
                    for key in sorted(loc.keys()):
                        d = edit_distance(search_term, key)
                        if d < best_match[1]:
                            best_match = (loc[key], d, key)

                match_len = max(len(best_match[2]), len(search_term))
                match_threshold = 0.4 + 0.2*match_len

                if best_match[1] <= match_threshold:
                    await message.channel.send(embed=best_match[0].get_embed())
                else:
                    if best_match[1] < match_threshold*2:
                        if best_match[2] in shortcuts:
                            await message.channel.send(
                                "I'm not sure what \"{0}\" is, did you mean \"{1}\"? "
                                "If so, you can use the shortcut \"{2}\".".format(
                                    search_term,
                                    str(best_match[0]).lower(),
                                    best_match[2]
                                )
                            )
                        else:
                            await message.channel.send("I'm not sure what \"{0}\" is, did you mean \"{1}\"?".format(search_term, best_match[2]))
                    else:
                        await message.channel.send("I'm not sure what \"{0}\" is.".format(search_term))


Hook.get("on_init").attach(on_init)
