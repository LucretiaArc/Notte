import random
import discord
import config
import data
import hook
import typing
import math

client = None
hdt_threshold_tables = {}
hdt_encounter_details = {}
hdt_encounter_difficulties = []
hdt_encounter_aliases = {}


async def on_init(discord_client):
    global client
    client = discord_client

    init_data()

    hook.Hook.get("public!xmus").attach(xmus)
    hook.Hook.get("public!threshold").attach(threshold)
    hook.Hook.get("on_mention").attach(handle_mention)


def init_data():
    global hdt_threshold_tables, hdt_encounter_details, hdt_encounter_difficulties, hdt_encounter_aliases
    hdt_threshold_tables = {
        "hms": {
            "standard": generate_threshold_table(7230, 3.6, [0, 7, 9, 15]),
            "expert": generate_threshold_table(9000, 3.7, [0, 15, 20, 25, 30, 35]),
            "master": generate_threshold_table(13000, 3.4, [0, 15, 20, 25, 30, 35]),
        },
        "hbh": {
            "standard": generate_threshold_table(7230, 4.8, [0, 7, 9, 15]),
            "expert": generate_threshold_table(9000, 4.75, [0, 15, 20, 35]),
            "master": generate_threshold_table(13000, 3.5, [0, 15, 20, 35]),
        },
        "hmc": {
            "standard": generate_threshold_table(7230, 2.75, [0, 7, 9, 15], 0, 1 / 1.1),
            "expert": generate_threshold_table(9000, 3.2, [0, 7, 9, 15]),
            "master": generate_threshold_table(13000, 2.4, [0, 7, 9, 15]),
        },
        "hjp": {
            "standard": generate_threshold_table(7230, 4.8, [0, 7, 9, 15, 22]),
            "expert": generate_threshold_table(9000, 4.2, [0, 7, 9, 15, 22]),
            "master": generate_threshold_table(13000, 2.6, [0, 7, 9, 15, 22]),
        },
        "hzd": {
            "standard": generate_threshold_table(7996, 4.4, [0, 7, 9, 15, 23]),
            "expert": generate_threshold_table(8386, 4.4, [0, 7, 9, 15, 23]),
        },
    }

    hdt_encounter_details = {
        "hms": {
            "name": "High Midgardsormr",
            "element": data.Element.WIND,
            "hint": {
                "standard": "Assumes a fire adventurer with MUB Glorious Tempest equipped.",
            }
        },
        "hbh": {
            "name": "High Brunhilda",
            "element": data.Element.FIRE,
            "hint": {
                "standard": "Assumes a water adventurer with MUB Volcanic Queen equipped.",
            }
        },
        "hmc": {
            "name": "High Mercury",
            "element": data.Element.WATER,
            "hint": {
                "standard": "Assumes a wind adventurer WITHOUT Queen of the Blue Seas equipped. "
                            "The High Mercury fight is based on meeting a DPS check, rather than meeting the HP check. "
                            "HP values assume that Lowen's S2 will be applied. ",
                "expert": "Assumes a wind adventurer with MUB Queen of the Blue Seas equipped.",
                "master": "Assumes a wind adventurer with MUB Queen of the Blue Seas equipped.",
            }
        },
        "hjp": {
            "name": "High Jupiter",
            "element": data.Element.LIGHT,
            "hint": {
                "standard": "Assumes a dark adventurer with MUB King of the Skies equipped. "
                            "HP values are those required to live the first Electron Outburst attack, which deals more damage than the initial HP check. "
                            "All 5* HJP bane void weapons (except the staff) provide a 7% defense bonus.",
                "expert": "Assumes a dark adventurer with MUB King of the Skies equipped.",
                "master": "Assumes a dark adventurer with MUB King of the Skies equipped.",
            }
        },
        "hzd": {
            "name": "High Zodiark",
            "element": data.Element.DARK,
            "hint": {
                "standard": "Assumes a light adventurer with MUB Ruler of Darkness equipped."
            }
        },
    }

    hdt_encounter_difficulties = ["standard", "expert", "master"]

    hdt_encounter_aliases = {}

    alias_lists = config.get_global("hdt_alias")
    for dragon, aliases in alias_lists.items():
        for alias in aliases+[dragon]:
            hdt_encounter_aliases[alias] = {"dragon": dragon, "difficulty": "standard"}
            for difficulty in hdt_encounter_difficulties:
                data_dict = {
                    "dragon": dragon,
                    "difficulty": difficulty
                }

                hdt_encounter_aliases[f"{difficulty} {alias}"] = data_dict
                hdt_encounter_aliases[f"{difficulty[0]}{alias}"] = data_dict
                hdt_encounter_aliases[f"{alias} {difficulty}"] = data_dict



async def xmus(message, args):
    """
    Posts a labelled X-Muspelheim pattern, so that groups playing High Brunhilda can negotiate where they're going to move to during that attack.
    """
    if message.channel.permissions_for(message.guild.me).attach_files:
        await message.channel.send("Pick an area for X-Muspelheim!", file=discord.File("../upload/xmus.png"))
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

    if encounter_alias in hdt_encounter_aliases:
        encounter_data = hdt_encounter_aliases[encounter_alias]
        dragon = encounter_data["dragon"]
        difficulty = encounter_data["difficulty"]

        if difficulty in hdt_threshold_tables[dragon]:
            details = hdt_encounter_details[dragon]
            name = details["name"]
            element = details["element"]
            hint = details["hint"].get(difficulty) or details["hint"]["standard"]
            table = hdt_threshold_tables[dragon][difficulty]

            embed = discord.Embed(
                title=f"{name} {difficulty.title()} HP Requirement",
                description=f"```\n{table}\n```",
                color=element.get_colour()
            ).set_footer(
                text=hint
            )

            await message.channel.send(embed=embed)
        else:
            await message.channel.send("I don't know the HP thresholds for that difficulty!")
    else:
        await message.channel.send("I haven't seen that high dragon before, they must be scary!")


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


def calc_threshold(strength, skill_multi, base_defense, defense_add, damage_multi):
    # see https://dragalialost.gamepedia.com/Damage_Formula
    defense = base_defense * (1 + defense_add/100)
    max_damage = math.floor((5/3) * (damage_multi * strength * skill_multi * 0.5 * 1.05) / defense)
    return max_damage + 1


def generate_threshold_table(strength, skill_multi, defense_mods, def_skill_mod=0, damage_multi=0.7125):
    table_rows = [
        ["Def", *map(lambda n: f"{n:+d}%", defense_mods)],
        ["Melee", *(calc_threshold(strength, skill_multi, 10, d + def_skill_mod, damage_multi) for d in defense_mods)],
        ["Ranged", *(calc_threshold(strength, skill_multi, 8, d + def_skill_mod, damage_multi) for d in defense_mods)]
    ]
    return generate_ascii_table(table_rows)


def generate_ascii_table(content: typing.List[list]):
    """
    Generates an ascii table from a list of rows
    :param content: list of rows containing values to put in the table
    :return: string containing ascii table
    """
    cb_h, cb_v = "─│"  # bar characters
    cc_ul, cc_ur, cc_bl, cc_br = "┌┐└┘"  # corner characters
    ct_u, ct_l, ct_r, ct_b = "┬├┤┴"  # T characters
    c_cross = "┼"  # cross character

    output = ""

    height = len(content)
    if height == 0:
        raise ValueError("Table must have at least one row")

    width = len(content[0])
    max_widths = [max((len(str(l[x])) for l in content)) for x in range(width)]  # max width for each column

    for y in range(height+1):
        # separator row
        if y == 0:
            left_cap = cc_ul
            right_cap = cc_ur + "\n"
            mid_connector = ct_u
        elif y == height:
            left_cap = cc_bl
            right_cap = cc_br
            mid_connector = ct_b
        else:
            left_cap = ct_l
            right_cap = ct_r + "\n"
            mid_connector = c_cross

        output += left_cap + mid_connector.join(cb_h * (w + 2) for w in max_widths) + right_cap

        # data row
        if y < height:
            row_content = " │ ".join(str(item).ljust(width) for item, width in zip(content[y], max_widths))
            output += f"│ {row_content} │\n"

    return output


hook.Hook.get("on_init").attach(on_init)
