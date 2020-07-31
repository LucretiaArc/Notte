import logging
import data
import hook
import natsort
import util
from collections import defaultdict
from fuzzy_match import Matcher

logger = logging.getLogger(__name__)

matcher: Matcher = None


async def on_init(discord_client):
    build_matcher()

    hook.Hook.get("public!printswith").attach(wyrmprint_lookup)
    hook.Hook.get("data_downloaded").attach(build_matcher)


async def wyrmprint_lookup(message, args):
    """
    Look for wyrmprints with a certain type of ability.
    `printswith <ability type>` gives a list of wyrmprints with abilities of that type.
    For example, `printswith stun res` gives a list of prints with Stun Res abilities.
    """
    match_content = matcher.match(args)
    if match_content:
        index = match_content[0]
        ab_names = natsort.natsorted(set(ab_name for ab_name in index), reverse=True)
        sections = []
        for name in ab_names:
            sections.append(util.get_emote("blank") + f" **{name}**\n" + "\n".join(sorted(index[name], reverse=True)))

        await util.send_long_message_in_sections(message.channel, sections, sep="\n")
    else:
        await message.channel.send("I don't know any wyrmprints that have an ability like that!")


def build_matcher():
    global matcher
    logger.info("Generating queries...")
    new_matcher = Matcher()

    wyrmprint_ability_index = defaultdict(lambda: defaultdict(list))
    wp: data.Wyrmprint
    for wp in data.Wyrmprint.get_all():
        abilities = list(map(lambda a: a[-1], filter(None, wp.get_abilities())))
        for i, ab in enumerate(abilities):
            if ab.generic_name and ab.name:
                other_abilities = list(map(lambda a: a.name, abilities[:i] + abilities[i+1:]))
                description_line = util.get_emote(f"rarity{wp.rarity or 0}") + f" {wp.name}"
                if other_abilities:
                    description_line += f" | {', '.join(other_abilities)}"
                wyrmprint_ability_index[ab.generic_name][ab.name].append(description_line)

    for gen_name, index in wyrmprint_ability_index.items():
        new_matcher.add(gen_name, index)

    matcher = new_matcher
    logger.info(f"{len(matcher.match_map)} queries generated")


hook.Hook.get("on_init").attach(on_init)
