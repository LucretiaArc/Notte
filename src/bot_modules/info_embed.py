import data
import re
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from hook import Hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    Hook.get("on_message").attach(get_info)


async def get_info(message):
    if "[[" in message.content:
        matches = re.findall(r"\[\[(.+?)\]\]", message.content.lower())
        if len(matches) > 0:
            search_locations = [
                data.Adventurer.adventurers,
                data.Dragon.dragons
            ]

            if len(matches) > 3:
                await client.send_message(message.channel, "Too many queries, only the first three will be shown.")

            for match in matches[:3]:
                search_term = match.lower()

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


Hook.get("on_init").attach(on_init)
