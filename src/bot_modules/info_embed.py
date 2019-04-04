import data
import re
import config
import logging
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from hook import Hook
import time

logger = logging.getLogger(__name__)

client = None
shortcuts = {}


async def on_init(discord_client):
    global client, shortcuts
    client = discord_client

    logger.info("Resolving query shortcuts")

    shortcut_config = config.get_global_config()["query_shortcuts"]
    entity_maps = {
        "adventurer": data.Adventurer.adventurers,
        "dragon": data.Dragon.dragons
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
            search_locations = [
                data.Adventurer.adventurers,
                data.Dragon.dragons,
                shortcuts
            ]

            if len(matches) > 3:
                await client.send_message(message.channel, "Too many queries, only the first three will be shown.")

            for match in matches[:3]:
                query_start_time = time.clock()
                if len(match) > 50:
                    await client.send_message(message.channel, "That's way too long, I'm not looking for that.")

                search_term = match.lower()

                # check shortcuts

                best_match = (None, 0, "")  # (matching item, match percent, match string)
                for loc in search_locations:
                    result = process.extractOne(search_term, loc.keys(), scorer=fuzz.ratio)
                    if result[1] > best_match[1]:
                        best_match = (loc.get(result[0]), result[1], result[0])

                match_len = max(len(best_match[2]), len(search_term))
                match_threshold = min(80.0, 90 - 60*2**(-0.45*match_len))
                if best_match[1] >= match_threshold:
                    await client.send_message(message.channel, embed=best_match[0].get_embed())
                else:
                    if best_match[1] > 0:
                        await client.send_message(message.channel, "I'm not sure what \"{0}\" is, did you mean \"{1}\"?".format(search_term, best_match[2]))
                    else:
                        await client.send_message(message.channel, "I'm not sure what \"{0}\" is.".format(search_term))

                logger.info("Info query for \"{0}\" took {1} seconds".format(search_term, time.clock() - query_start_time))


Hook.get("on_init").attach(on_init)
