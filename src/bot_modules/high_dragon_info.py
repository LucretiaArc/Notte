import discord
from hook import Hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    Hook.get("public!xmus").attach(xmus)
    Hook.get("public!threshold").attach(threshold)


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


async def threshold(message, args):
    """
    Shows tables for high dragon HP requirements.
    `threshold <dragon>` gives the table for a dragon.
    """
    tables = {
        "hms": "┌────────┬──────┬──────┬──────┬──────┬──────┐\n"
               "│ Def    │ +0%  │ +7%  │ +9%  │ +11% │ +15% │\n"
               "├────────┼──────┼──────┼──────┼──────┼──────┤\n"
               "│ Melee  │ 1624 │ 1518 │ 1490 │ 1463 │ 1412 │\n"
               "├────────┼──────┼──────┼──────┼──────┼──────┤\n"
               "│ Ranged │ 2029 │ 1897 │ 1862 │ 1828 │ 1765 │\n"
               "└────────┴──────┴──────┴──────┴──────┴──────┘\n",
        "hbh": "┌────────┬──────┬──────┬──────┬──────┬──────┐\n"
               "│ Def    │ +0%  │ +7%  │ +9%  │ +11% │ +15% │\n"
               "├────────┼──────┼──────┼──────┼──────┼──────┤\n"
               "│ Melee  │ 2165 │ 2023 │ 1986 │ 1950 │ 1882 │\n"
               "├────────┼──────┼──────┼──────┼──────┼──────┤\n"
               "│ Ranged │ 2705 │ 2529 │ 2482 │ 2437 │ 2353 │\n"
               "└────────┴──────┴──────┴──────┴──────┴──────┘\n",
    }

    aliases = {
        "high mid": "hms",
        "high midgard": "hms",
        "high midgardsormr": "hms",
        "hmid": "hms",
        "mid": "hms",
        "midgard": "hms",
        "midgardsormr": "hms",
        "high brun": "hbh",
        "high brunhilda": "hbh",
        "hbrun": "hbh",
        "brun": "hbh",
        "brunhilda": "hbh"
    }

    dragon = args.strip().lower()
    if dragon == "":
        await message.channel.send("Please me know which dragon you'd like the thresholds for.")
        return

    if dragon in aliases:
        dragon = aliases[dragon]
    if dragon in tables:
        await message.channel.send("Please be sure that your adventurer is on-element, and has the appropriate wyrmprint equipped!\n"
                                   "```\n" + tables[dragon] + "```")
    else:
        await message.channel.send("I haven't seen that high dragon before, they must be scary!")

Hook.get("on_init").attach(on_init)
