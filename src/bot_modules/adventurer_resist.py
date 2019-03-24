import collections
import json
import urllib.parse
import urllib.request
import logging
import re
import util
from hook import Hook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = None
resist_data = None
adventurer_data = None

elemental_types = {
    "flame": "fire",
    "water": "water",
    "wind": "wind",
    "light": "light",
    "shadow": "dark"
}
weapon_types = ["sword", "blade", "dagger", "axe", "lance", "bow", "wand", "staff"]
res_names = {
    "poison": "poison",
    "burning": "burn",
    "freezing": "freeze",
    "paralysis": "paralysis",
    "blindness": "blind",
    "stun": "stun",
    "curses": "curse",
    "bog": "bog",
    "sleep": "sleep"
}


def on_init(discord_client):
    global client
    client = discord_client
    update_data_store()

    Hook.get("on_reset").attach(update_data_store)
    Hook.get("public!resist").attach(resist_search)


async def resist_search(message, args):
    """
    Searches for combinations of elemental affinity and affliction resistance.
    **Affliction keywords:** *poison, burning/burn, freezing/freeze, paralysis, blind, stun, curses/curse, bog, sleep*
    **Element keywords:** *flame/fire, water, wind, light, shadow/dark*
    If no keywords of a category are used, all keywords of that category are included. (E.g. if no element is specified, adventurers of all elements will be included)
    If you use more than one keyword from a single category, or omit a category, all other categories must have *exactly* one keyword specified.
    You may also add a number as the minimum percentage resist value to display. If multiple are provided, only the first will be used.

    Shortcut keywords are available for Advanced Dragon Trials:
    **hms** (High Midgardsormr) = *flame*, *stun*, *100*
    **hbh** (High Brunhilda) = *water*, *burning*, *100*

    """
    arg_list = list(map(str.strip, args.lower().split(" ")))

    shortcuts = {
        "hms": ("fire", "stun", 100),
        "hbh": ("water", "burn", 100),
    }

    specified_elements = set()
    specified_resists = set()
    specified_threshold = -1

    # collect criteria
    for arg in arg_list:
        if arg == "":
            continue

        if arg in shortcuts:
            specified_elements.add(shortcuts[arg][0])
            specified_resists.add(shortcuts[arg][1])
            specified_threshold = shortcuts[arg][2]
            continue

        if arg in elemental_types:
            arg = elemental_types[arg]
        elif arg in res_names:
            arg = res_names[arg]

        if arg in elemental_types.values():
            specified_elements.add(arg)
        elif arg in res_names.values():
            specified_resists.add(arg)

        # find threshold
        if specified_threshold == -1:
            threshold_match = re.findall("^(\d+)%?$", arg)
            if len(threshold_match) > 0 and 0 <= int(threshold_match[0]) <= 100:
                specified_threshold = int(threshold_match[0])

    # if one is empty, use all
    if len(specified_elements) == 0:
        element_list = elemental_types.values()
    else:
        element_list = specified_elements
    if len(specified_resists) == 0:
        resist_list = res_names.values()
    else:
        resist_list = specified_resists

    # too broad or no keywords
    if len(element_list) == 0 and len(resist_list) == 0:
        await client.send_message(message.channel, "I something to work with, give me an element or resistance!")
        return
    elif len(resist_list) > 1 and len(element_list) > 1:
        await client.send_message(message.channel, "Too much! Try narrowing down your search.")
        return

    result_sections = []
    for res in resist_list:
        match_list = []
        for el in element_list:
            match_list.extend(((
                name,
                adventurer_data[name]["element"],
                adventurer_data[name]["rarity"],
                resist_data[res][el][name]
            ) for name in resist_data[res][el]))

        if len(match_list) > 0 or res in specified_resists:  # include resists specifically searched for
            result_string = util.get_emote(res) + "** " + res.capitalize() + " Resistance**\n"
        else:
            continue

        if len(match_list) == 0:
            result_string += util.get_emote("blank")*2 + " *No results.*"
            result_sections.append(result_string)
            continue

        # sorting
        match_list.sort(key=lambda t: t[0])  # by name
        match_list.sort(key=lambda t: t[1])  # by element
        match_list.sort(key=lambda t: t[2], reverse=True)  # by rarity
        match_list.sort(key=lambda t: t[3], reverse=True)  # by percent

        # formatting
        current_resist = 101
        for adv in match_list:
            if adv[3] < specified_threshold:
                break

            if adv[3] < current_resist:
                if current_resist < 101:  # don't separate the resist header from the first section
                    result_sections.append(result_string)
                    result_string = ""
                current_resist = adv[3]
                result_string += util.get_emote("blank")*2 + " **" + str(adv[3]) + "%**"

            result_string += "\n" + util.get_emote("rarity" + str(adv[2])) + \
                             util.get_emote(list(elemental_types.values())[adv[1]]) + " " + adv[0]

        result_sections.append(result_string)

    if len(result_sections) == 0:
        await client.send_message(message.channel, "I didn't find anything! Maybe there's nobody that matches your search?")

    # avoid huge messages by breaking them up at every resist
    output_message = ""
    for section in result_sections:
        section = section.strip()
        if len(output_message + "\n" + section) > 2000:
            await client.send_message(message.channel, output_message)
            output_message = section
        else:
            output_message += "\n" + section

    await client.send_message(message.channel, output_message)


def fetch_resist_abilities():
    """
    Gets info about all the resist skills in the game. Each element of the list is a dict with the keys
    (skill_id, resist_type, resist_value), and a skill will appear once for each resistance type it provides.
    :return: a list of dicts, representing all the resist skills in the game
    """
    request = "https://dragalialost.gamepedia.com/api.php?action=cargoquery&tables=Abilities&format=json&limit=500" \
              "&fields=Details,Id" \
              "&where=Details+LIKE+'%susceptibility%'"

    with urllib.request.urlopen(request) as response:
        ability_info_list = json.loads(response.read().decode())["cargoquery"]

        abilities = [
            {
                "id": int(d["title"]["Id"]),
                "details": d["title"]["Details"]
            }
            for d in ability_info_list
        ]

        res_abilities = []
        for ability in abilities:
            resist_percent = int(re.findall("'''(\d+)%'''", ability["details"])[0])
            for res in res_names:
                if res in ability["details"]:
                    res_abilities.append({
                        "ability_id": ability["id"],
                        "resist_type": res_names[res],
                        "resist_value": resist_percent
                    })

        return res_abilities


def fetch_adventurer_data():
    request = "https://dragalialost.gamepedia.com/api.php?action=cargoquery&tables=Adventurers&format=json&limit=500" \
              "&fields=FullName,Rarity,ElementalTypeId,WeaponTypeId"

    with urllib.request.urlopen(request) as response:
        adventurer_info_list = json.loads(response.read().decode())["cargoquery"]

        adventurer_info = {
            a["title"]["FullName"]: {
                "name": a["title"]["FullName"],
                "rarity": int(a["title"]["Rarity"]),
                "element": int(a["title"]["ElementalTypeId"]) - 1,
                "weapon": int(a["title"]["WeaponTypeId"]) - 1,
            } for a in adventurer_info_list
        }

        return adventurer_info


def fetch_adventurer_resists(res_abilities):
    res_data = {res: {el: collections.defaultdict(int) for el in elemental_types.values()} for res in res_names.values()}

    request = "https://dragalialost.gamepedia.com/api.php?action=cargoquery&tables=Adventurers&format=json&limit=500" \
              "&fields=FullName,ElementalType," \
              "Abilities11,Abilities12,Abilities13,Abilities14," \
              "Abilities21,Abilities22,Abilities23,Abilities24," \
              "Abilities31,Abilities32,Abilities33,Abilities34"

    with urllib.request.urlopen(request) as response:
        adventurer_info_list = json.loads(response.read().decode())["cargoquery"]

        adventurers = [
            {
                "name": a["title"]["FullName"],
                "element": elemental_types[a["title"]["ElementalType"].lower()],
                "abilities": [
                    [
                        int(a["title"]["Abilities34"]),
                        int(a["title"]["Abilities33"]),
                        int(a["title"]["Abilities32"]),
                        int(a["title"]["Abilities31"])
                    ], [
                        int(a["title"]["Abilities24"]),
                        int(a["title"]["Abilities23"]),
                        int(a["title"]["Abilities22"]),
                        int(a["title"]["Abilities21"])
                    ], [
                        int(a["title"]["Abilities14"]),
                        int(a["title"]["Abilities13"]),
                        int(a["title"]["Abilities12"]),
                        int(a["title"]["Abilities11"])
                    ]
                ]
            }
            for a in adventurer_info_list
        ]

        for adv in adventurers:
            for ability_set in adv["abilities"]:
                for ability_id in ability_set:
                    ability_is_resist = False
                    if ability_id > 0:
                        for check_ab in res_abilities:
                            if ability_id == check_ab["ability_id"]:
                                ability_is_resist = True
                                res_data[check_ab["resist_type"]][adv["element"]][adv["name"]] += check_ab["resist_value"]

                    if ability_is_resist:
                        break

        return res_data


def update_data_store():
    global resist_data, adventurer_data

    logger.info("Requesting resist abilities")
    res_abilities = fetch_resist_abilities()
    logger.info("Finished processing resist abilities, requesting adventurer resists")
    resist_data = fetch_adventurer_resists(res_abilities)
    logger.info("Finished processing adventurer resists, requesting adventurer info")
    adventurer_data = fetch_adventurer_data()
    logger.info("Finished processing adventurer info, data stores updated")


Hook.get("on_init").attach(on_init)
