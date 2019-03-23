from hook import Hook

client = None
config = None


async def on_init(discord_client, module_config):
    global client, config
    client = discord_client
    config = module_config

    Hook.get("public!xmus").attach(xmus)
    Hook.get("public!threshold").attach(threshold)


async def xmus(message, args):
    """
    Posts a labelled X-Muspelheim pattern, so that groups playing High Brunhilda can negotiate where they're going to move to during that attack.
    """
    await client.send_file(message.channel, "../assets/images/xmus.png")


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
        "mid": "hms",
        "midgard": "hms",
        "midgardsormr": "hms",
        "high brun": "hbh",
        "high brunhilda": "hbh",
        "brun": "hbh",
        "brunhilda": "hbh"
    }

    dragon = args.strip().lower()
    if dragon == "":
        await client.send_message(message.channel, "Please me know which dragon you'd like the thresholds for.")
        return

    if dragon in aliases:
        dragon = aliases[dragon]
    if dragon in tables:
        await client.send_message(message.channel,
                                  "Please be sure that your adventurer is on-element, and has the appropriate wyrmprint equipped!\n"
                                  "```\n" + tables[dragon] + "```")
    else:
        await client.send_message(message.channel, "I haven't seen that high dragon before, they must be scary!")

Hook.get("on_init").attach(on_init)
