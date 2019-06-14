import discord
import config
import data
import hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    hook.Hook.get("public!xmus").attach(xmus)
    hook.Hook.get("public!bubbles").attach(bubbles)
    hook.Hook.get("public!threshold").attach(threshold)


async def xmus(message, args):
    """
    Posts a labelled X-Muspelheim pattern, so that groups playing High Brunhilda can negotiate where they're going to move to during that attack.
    """
    if message.channel.permissions_for(message.guild.me).attach_files:
        await message.channel.send("Pick an area for X-Muspelheim!", file=discord.File("../assets/images/xmus.png"))
    elif message.channel.permissions_for(message.guild.me).embed_links:
        await message.channel.send("Pick an area for X-Muspelheim! https://cdn.discordapp.com/attachments/560454966154756107/560455072073646082/xmus.png")
    else:
        await message.channel.send("Pick an area for X-Muspelheim! https://cdn.discordapp.com/attachments/560454966154756107/560455072073646082/xmus.png\n"
                                   "A is top\n"
                                   "B is right\n"
                                   "C is bottom\n"
                                   "D is left")


async def bubbles(message, args):
    """
    Posts a labelled Spheres of Salvation pattern, so that groups playing High Mercury can negotiate where they're going to move to during that attack.
    """
    if message.channel.permissions_for(message.guild.me).attach_files:
        await message.channel.send("Pick a bubble for Spheres of Salvation!", file=discord.File("../assets/images/bubbles.png"))
    elif message.channel.permissions_for(message.guild.me).embed_links:
        await message.channel.send("Pick a bubble for Spheres of Salvation! https://cdn.discordapp.com/attachments/560454966154756107/568706931515064330/bubbles.png")
    else:
        await message.channel.send("Pick a bubble for Spheres of Salvation! https://cdn.discordapp.com/attachments/560454966154756107/568706931515064330/bubbles.png\n"
                                   "A to D from left to right.")


async def threshold(message, args):
    """
    Shows tables for high dragon HP requirements.
    `threshold <dragon>` gives the table for a dragon.
    """
    tables = {
        "hbh": "┌────────┬──────┬──────┬──────┬──────┬──────┐\n"
               "│ Def    │ +0%  │ +7%  │ +9%  │ +11% │ +15% │\n"
               "├────────┼──────┼──────┼──────┼──────┼──────┤\n"
               "│ Melee  │ 2165 │ 2023 │ 1986 │ 1950 │ 1882 │\n"
               "├────────┼──────┼──────┼──────┼──────┼──────┤\n"
               "│ Ranged │ 2705 │ 2529 │ 2482 │ 2437 │ 2353 │\n"
               "└────────┴──────┴──────┴──────┴──────┴──────┘\n",
        "hmc": "┌────────┬──────┬──────┬──────┬──────┬──────┐\n"
               "│ Def    │ +0%  │ +7%  │ +9%  │ +11% │ +15% │\n"
               "├────────┼──────┼──────┼──────┼──────┼──────┤\n"
               "│ Melee  │ 1218 │ 1138 │ 1118 │ 1097 │ 1059 │\n"
               "├────────┼──────┼──────┼──────┼──────┼──────┤\n"
               "│ Ranged │ 1522 │ 1423 │ 1397 │ 1372 │ 1324 │\n"
               "└────────┴──────┴──────┴──────┴──────┴──────┘\n",
        "hms": "┌────────┬──────┬──────┬──────┬──────┬──────┐\n"
               "│ Def    │ +0%  │ +7%  │ +9%  │ +11% │ +15% │\n"
               "├────────┼──────┼──────┼──────┼──────┼──────┤\n"
               "│ Melee  │ 1624 │ 1518 │ 1490 │ 1463 │ 1412 │\n"
               "├────────┼──────┼──────┼──────┼──────┼──────┤\n"
               "│ Ranged │ 2029 │ 1897 │ 1862 │ 1828 │ 1765 │\n"
               "└────────┴──────┴──────┴──────┴──────┴──────┘\n",
        "hjp": "┌────────┬──────┬──────┬──────┬──────┬──────┐\n"
               "│ Def    │ +0%  │ +7%  │ +9%  │ +11% │ +15% │\n"
               "├────────┼──────┼──────┼──────┼──────┼──────┤\n"
               "│ Melee  │ ???? │ ???? │ ???? │ ???? │ ???? │\n"
               "├────────┼──────┼──────┼──────┼──────┼──────┤\n"
               "│ Ranged │ ???? │ ???? │ ???? │ ???? │ ???? │\n"
               "└────────┴──────┴──────┴──────┴──────┴──────┘\n",
        "hzd": "┌────────┬──────┬──────┬──────┬──────┬──────┐\n"
               "│ Def    │ +0%  │ +7%  │ +9%  │ +11% │ +15% │\n"
               "├────────┼──────┼──────┼──────┼──────┼──────┤\n"
               "│ Melee  │ ???? │ ???? │ ???? │ ???? │ ???? │\n"
               "├────────┼──────┼──────┼──────┼──────┼──────┤\n"
               "│ Ranged │ ???? │ ???? │ ???? │ ???? │ ???? │\n"
               "└────────┴──────┴──────┴──────┴──────┴──────┘\n"
    }

    # (proper name, adventurer element, wyrmprint name, dragon element, extra text)
    encounter_details = {
        "hbh": (
            "High Brunhilda",
            data.Element.FIRE,
            data.Element.WATER,
            "Assumes a {0} adventurer with MUB Volcanic Queen equipped."
        ),
        "hmc": (
            "High Mercury",
            data.Element.WATER,
            data.Element.WIND,
            "The High Mercury fight is based on meeting a soft strength requirement, rather than meeting the HP check. "
            "It is recommended that you bring a {0} adventurer with as much offensive power as possible to avoid timing out. "
            "In general, try to have at least 2.6k strength before attempting the fight."
        ),
        "hms": (
            "High Midgardsormr",
            data.Element.WIND,
            data.Element.FIRE,
            "Assumes a {0} adventurer with MUB Glorious Tempest equipped."
        ),
        "hjp": (
            "High Jupiter",
            data.Element.LIGHT,
            data.Element.DARK,
            "Assumes a {0} adventurer with the appropriate wyrmprint equipped."
        ),
        "hzd": (
            "High Zodiark",
            data.Element.DARK,
            data.Element.LIGHT,
            "Assumes a {0} adventurer with the appropriate wyrmprint equipped."
        )
    }

    replacements = config.get_global_config()["high_dragon_shortcuts"]

    dragon = args.strip().lower()
    if dragon == "":
        await message.channel.send("Please me know which dragon you'd like the thresholds for.")
        return

    if dragon in replacements:
        dragon = replacements[dragon]
    if dragon in tables:
        details = encounter_details[dragon]
        embed = discord.Embed(
            title="{0} HP Requirement".format(details[0]),
            description="```\n" + tables[dragon] + "\n```",
            color=details[1].get_colour()
        )
        embed.set_footer(text=details[3].format(str(details[2]).lower()))
        await message.channel.send(embed=embed)
    else:
        await message.channel.send("I haven't seen that dragon before, they must be scary!")

hook.Hook.get("on_init").attach(on_init)
