import random
import discord
import config
import data
import hook
import typing
import math
import util

client = None
hdt_encounter_queries = {}


async def on_init(discord_client):
    global client, hdt_encounter_queries
    client = discord_client
    hdt_encounter_queries = generate_queries()

    hook.Hook.get("public!xmus").attach(xmus)
    hook.Hook.get("public!whirlpools").attach(whirlpools)
    hook.Hook.get("public!threshold").attach(threshold)
    hook.Hook.get("on_mention").attach(handle_mention)


def generate_queries():
    queries = {}
    hdt_data = config.get_global("hdt_data")
    alias_lists = config.get_global("hdt_alias")

    for hdt, dragon_info in hdt_data.items():
        dragon_name = dragon_info["dragon_name"]
        dragon_element = data.Element(dragon_info["dragon_element"])
        resist_wyrmprint_name = dragon_info["wyrmprint"]
        aliases = alias_lists[hdt] + [hdt]
        for difficulty, difficulty_info in dragon_info["fight_info"].items():
            embed = discord.Embed(
                title=f"High {dragon_name} {difficulty.title()} HP Requirement",
                description=generate_description(resist_wyrmprint_name, difficulty_info),
                color=dragon_element.get_colour()
            )

            for alias in aliases:
                queries[f"{difficulty} {alias}"] = embed
                queries[f"{difficulty[0]}{alias}"] = embed
                queries[f"{alias} {difficulty}"] = embed

    return queries


async def xmus(message, args):
    """
    Posts a labelled X-Muspelheim pattern, so that groups playing High Brunhilda can negotiate where they're going to move to during that attack.
    """
    if message.channel.permissions_for(message.guild.me).attach_files:
        await message.channel.send("Pick an area for X-Muspelheim!", file=discord.File(util.path("assets/xmus.png")))
    elif message.channel.permissions_for(message.guild.me).embed_links:
        await message.channel.send(
            "Pick an area for X-Muspelheim! https://cdn.discordapp.com/attachments/560454966154756107/560455072073646082/xmus.png")
    else:
        await message.channel.send(
            "Pick an area for X-Muspelheim! https://cdn.discordapp.com/attachments/560454966154756107/560455072073646082/xmus.png\n"
            "A is top\n"
            "B is right\n"
            "C is bottom\n"
            "D is left")


async def whirlpools(message, args):
    """
    Posts a diagram for Master High Mercury's whirlpool attack, to indicate where the safe zones are.
    """
    if message.channel.permissions_for(message.guild.me).attach_files:
        await message.channel.send(file=discord.File(util.path("assets/whirlpools.png")))
    elif message.channel.permissions_for(message.guild.me).embed_links:
        await message.channel.send(
            "https://cdn.discordapp.com/attachments/560454966154756107/641107074469724201/whirlpools.png")
    else:
        await message.channel.send(
            "https://cdn.discordapp.com/attachments/560454966154756107/641107074469724201/whirlpools.png\n"
            "If four whirlpools appear, safe zones are on the left and the bottom.\n"
            "If three whirlpools appear, the safe zone is on the top.")


async def threshold(message, args):
    """
    Shows tables for high dragon HP requirements.
    `threshold <encounter>` gives the table for an encounter.
    The encounter has two key parts (a dragon and a difficulty), and both are required for threshold information.
    """

    encounter_alias = args.strip().lower()

    if encounter_alias == "":
        await message.channel.send("Please me know which dragon you'd like the thresholds for.")
        return

    if encounter_alias in hdt_encounter_queries:
        await message.channel.send(embed=hdt_encounter_queries[encounter_alias])
    else:
        await message.channel.send("I don't know thresholds for that, sorry!")


async def handle_mention(message):
    if "which hdt" in message.content.lower():
        dragon = random.choice([
            "Midgardsormr",
            "Brunhilda",
            "Mercury",
            "Jupiter",
            "Zodiark"
        ])
        await message.channel.send(f"You should play High {dragon}'s Trial!")


def generate_description(print_name: str, fight_info: dict):
    # print damage reduction multiplier is 0.7125
    strength, skill_multi, def_mods = fight_info["str"], fight_info["hp_check_multi"], fight_info["recommended_def"]
    table_a = generate_threshold_table(strength, skill_multi, def_mods, 0, 0.7125)
    table_b = generate_threshold_table(strength, skill_multi, def_mods, 0, 1)
    return f"With {print_name} equipped:\n```\n{table_a}```\nWithout {print_name} equipped:\n```\n{table_b}```"


def generate_threshold_table(strength, skill_multi, defense_mods, def_skill_mod=0, damage_multi=0.7125):
    table_rows = [
        ["Def", *map(lambda n: f"{n:+d}%", defense_mods)],
        ["Melee", *(calc_threshold(strength, skill_multi, 10, d + def_skill_mod, damage_multi) for d in defense_mods)],
        ["Ranged", *(calc_threshold(strength, skill_multi, 8, d + def_skill_mod, damage_multi) for d in defense_mods)]
    ]
    return generate_ascii_table(table_rows)


def calc_threshold(strength, skill_multi, base_defense, defense_add, damage_multi):
    # see https://dragalialost.gamepedia.com/Damage_Formula
    defense = base_defense * (1 + defense_add/100)
    max_damage = math.floor((5/3) * (damage_multi * strength * skill_multi * 0.5 * 1.05) / defense)
    return max_damage + 1


def generate_ascii_table(content: typing.List[list]):
    """
    Generates an ascii table from a list of rows
    :param content: list of rows containing values to put in the table
    :return: string containing ascii table
    """
    char_bar_h, char_bar_v = "─│"  # bar characters
    char_corner_tl, char_corner_tr, char_corner_bl, char_corner_br = "┌┐└┘"  # corner characters
    char_tack_t, char_tack_l, char_tack_r, char_tack_b = "┬├┤┴"  # T characters
    char_cross = "┼"  # cross character

    output = ""

    height = len(content)
    if height == 0:
        raise ValueError("Table must have at least one row")

    width = len(content[0])
    max_widths = [max((len(str(row[x])) for row in content)) for x in range(width)]  # max width for each column

    # generate table rows
    for y in range(height+1):
        # separator (non-data) row
        if y == 0:
            left_cap = char_corner_tl
            right_cap = char_corner_tr + "\n"
            mid_connector = char_tack_t
        elif y == height:
            left_cap = char_corner_bl
            right_cap = char_corner_br
            mid_connector = char_tack_b
        else:
            left_cap = char_tack_l
            right_cap = char_tack_r + "\n"
            mid_connector = char_cross

        output += left_cap + mid_connector.join(char_bar_h * (w + 2) for w in max_widths) + right_cap

        # data row
        if y < height:
            row_content = " │ ".join(str(item).ljust(width) for item, width in zip(content[y], max_widths))
            output += f"│ {row_content} │\n"

    return output


hook.Hook.get("on_init").attach(on_init)
