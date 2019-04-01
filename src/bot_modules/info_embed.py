import data
import re
import discord
import util
import string
from hook import Hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    Hook.get("on_message").attach(get_info)


def get_adventurer_embed(adv: data.Adventurer):
    embed_colours = [
        0xFF0000,
        0x0066FF,
        0x00CC00,
        0xFFBB00,
        0xAA00DD
    ]

    header = "".join(map(util.get_emote, (
        "rarity" + str(adv.rarity),
        adv.element,
        adv.weapon_type
    ))) + " {0}: {1}".format(adv.name, adv.title)

    desc = "{0} HP  /  {1} Str  /  {2} Might\n\n" \
           "**Skills**\n" \
           "{3}\n{4}\n\n" \
           "**Abilities**\n" \
           "{5}\n{6}\n{7}\n\n" \
           "**Co-ability:** {8}\n\n" \
           "*Obtained from:  {9}*\n" \
           "*Release Date:  {10}*\n".format(
                adv.max_hp, adv.max_str, adv.max_might,
                adv.skill_1.name, adv.skill_2.name,
                adv.ability_1[-1].name, adv.ability_2[-1].name, adv.ability_3[-1].name,
                adv.coability[-1].name,
                adv.obtained,
                adv.release_date,
            )

    embed = discord.Embed(
        title=header,
        description=desc,
        colour=embed_colours[adv.element.value-1],
    )

    return embed


async def get_info(message):
    if "[[" in message.content:
        matches = re.findall(r"\[\[(.+?)\]\]", message.content.lower())
        found_result = False
        for search in matches:
            adv_name = string.capwords(search)
            if adv_name in data.Adventurer.adventurers:
                adv = data.Adventurer.adventurers[adv_name]
                await client.send_message(message.channel, embed=get_adventurer_embed(adv))
                found_result = True

        if not found_result:
            await client.send_message(message.channel, "I don't know what you're looking for. Try the name of an adventurer!")


Hook.get("on_init").attach(on_init)
