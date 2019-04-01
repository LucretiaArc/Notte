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

    header_str = "{0}{1}{2} {3}: {4}".format(
        util.get_emote("rarity" + str(adv.rarity)),
        util.get_emote(adv.element or ""),
        util.get_emote(adv.weapon_type or ""),
        adv.name or "???",
        adv.title or "???"
    )

    stats_str = "{0} HP  /  {1} Str  /  {2} Might\n\n".format(
        adv.max_hp or "???",
        adv.max_str or "???",
        adv.max_might or "???"
    )

    skill_str = "**Skills**\n{0}\n{1}\n\n".format(
        "???" if (not adv.skill_1 or not adv.skill_1.name) else adv.skill_1.name,
        "???" if (not adv.skill_2 or not adv.skill_2.name) else adv.skill_2.name,
    )

    ability_str = "**Abilities**\n{0}\n{1}\n{2}\n\n".format(
        "???" if (not adv.ability_1 or not adv.ability_1[-1].name) else adv.ability_1[-1].name,
        "???" if (not adv.ability_2 or not adv.ability_2[-1].name) else adv.ability_2[-1].name,
        "???" if (not adv.ability_3 or not adv.ability_3[-1].name) else adv.ability_3[-1].name
    )

    try:
        cab_min = adv.coability[0].name or "???"
        cab_max = adv.coability[-1].name or "???"
        coability_str = "**Co-ability:** {0}({1}-{2})%\n\n".format(
            cab_min[:cab_min.index("+") + 1],
            re.findall(r"(\d+)%", cab_min)[0],
            re.findall(r"(\d+)%", cab_max)[0]
        )
    except (IndexError, ValueError, TypeError):
        coability_str = "**Co-ability:** ???\n\n"

    footer_str = "*Obtained from:  {0}*\n*Release Date:  {1}*".format(
        adv.obtained or "???",
        adv.release_date or "???"
    )

    desc = "".join((
        stats_str,
        skill_str,
        ability_str,
        coability_str,
        footer_str
    ))

    if adv.element is not None:
        embed = discord.Embed(
            title=header_str,
            description=desc,
            colour=embed_colours[adv.element.value-1]
        )
    else:
        embed = discord.Embed(
            title=header_str,
            description=desc
        )

    return embed


async def get_info(message):
    if "[[" in message.content:
        matches = re.findall(r"\[\[(.+?)\]\]", message.content.lower())
        if len(matches) > 0:
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
