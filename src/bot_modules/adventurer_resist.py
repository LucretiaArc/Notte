import collections
import logging
import re
import util
import data
import config
import hook

logger = logging.getLogger(__name__)

resist_data = None


async def on_init(discord_client):
    hook.Hook.get("data_downloaded").attach(update_data_store)
    hook.Hook.get("public!resist").attach(resist_search)

    await update_data_store()


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
    **hmc** (High Mercury) = *wind*, *bog*, *100*
    **hjp** (High Jupiter) = *dark*, *paralysis*, *100*
    **hzd** (High Zodiark) = *light*, *curse*, *100*

    """
    args = args.lower()
    alias_lists = config.get_global("hdt_alias")
    for hdt, aliases in alias_lists.items():
        for alias in aliases:
            args = args.replace(alias, hdt)

    arg_list = list(map(str.strip, args.split(" ")))

    shortcuts = {
        "hbh": (data.Element.WATER, data.Resistance.BURN, 100),
        "hmc": (data.Element.WIND, data.Resistance.BOG, 100),
        "hms": (data.Element.FIRE, data.Resistance.STUN, 100),
        "hjp": (data.Element.DARK, data.Resistance.PARALYSIS, 100),
        "hzd": (data.Element.LIGHT, data.Resistance.CURSE, 100),
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
            if specified_threshold == -1:
                specified_threshold = shortcuts[arg][2]
            continue

        try:
            specified_elements.add(data.Element(arg.capitalize()))
            continue
        except ValueError:
            pass

        try:
            specified_resists.add(data.Resistance(arg.capitalize()))
            continue
        except ValueError:
            pass

        # find threshold
        if specified_threshold == -1:
            threshold_match = re.findall(r"^(\d+)%?$", arg)
            if len(threshold_match) > 0 and 0 <= int(threshold_match[0]) <= 100:
                specified_threshold = int(threshold_match[0])

    # if one is empty, use all
    if len(specified_elements) == 0:
        element_list = list(data.Element)
    else:
        element_list = specified_elements
    if len(specified_resists) == 0:
        resist_list = list(data.Resistance)
    else:
        resist_list = specified_resists

    # too broad or no keywords
    if len(specified_elements) == 0 and len(specified_resists) == 0:
        await message.channel.send("I need something to work with, give me an element or resistance!")
        return
    elif len(resist_list) > 1 and len(element_list) > 1:
        await message.channel.send("Too much! Try narrowing down your search.")
        return

    result_lines = []
    emote = util.get_emote
    for res in resist_list:
        match_list = []
        for el in element_list:
            match_list.extend(list(filter(None, map(data.Adventurer.find, resist_data[res][el]))))

        if len(match_list) > 0 or res in specified_resists:  # include resists specifically searched for
            result_lines.append(f"{emote(res)} **{res} Resistance**")
        else:
            continue

        if len(match_list) == 0:
            result_lines.append(f"{emote('blank')*2} *No results.* ")
            continue

        # sorting
        match_list.sort(key=lambda a: a.full_name)  # by name
        match_list.sort(key=lambda a: a.element.value)  # by element
        match_list.sort(key=lambda a: a.rarity, reverse=True)  # by rarity
        match_list.sort(key=lambda a: resist_data[res][a.element][a.get_key()], reverse=True)  # by percent

        # formatting
        current_resist = 101
        for adv in match_list:
            adv_res_percent = resist_data[res][adv.element][adv.get_key()]
            if adv_res_percent < specified_threshold:
                break

            if adv_res_percent < current_resist:
                current_resist = adv_res_percent
                result_lines.append(f"{emote('blank')*2} **{adv_res_percent}%**")

            result_lines.append(f"{emote('rarity' + str(adv.rarity))}{emote(adv.element)} {adv.full_name}")

    if len(result_lines) == 0:
        await message.channel.send("I didn't find anything! Maybe there's nobody that matches your search?")

    await util.send_long_message_in_sections(message.channel, result_lines)


async def index_adventurer_resists():
    res_data = {res: {e: collections.defaultdict(int) for e in data.Element} for res in data.Resistance}

    def get_ability_resists(ability: data.Ability):
        if "susceptibility" not in ability.description:
            return None
        value_matches = re.findall(r"(\d+)%", ability.description)
        if len(value_matches) == 0:
            logger.warning(f"Ability {ability.name} ({ability.id}) appears to be a resist ability, but has no resist percentage listed")
            return None

        ability_resistances = []

        resist_percent = int(value_matches[0])
        for res in data.Resistance:
            if any(i in ability.description.casefold() for i in map(str.casefold, res.values)):
                ability_resistances.append((res, resist_percent))

        return ability_resistances

    for adv in data.Adventurer.get_all():
        adv_resistances = []
        for ab in adv.get_abilities():
            if ab:
                adv_resistances += get_ability_resists(ab[-1]) or [None]

        for res in filter(None, adv_resistances):
            res_data[res[0]][adv.element][adv.get_key()] += res[1]

    return res_data


async def update_data_store():
    global resist_data

    logger.info("Indexing adventurer resistances...")
    resist_data = await index_adventurer_resists()
    logger.info("Finished indexing adventurer resistances.")


hook.Hook.get("on_init").attach(on_init)
