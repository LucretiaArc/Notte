import data
import typing
import config
import collections
import textwrap
import natsort
import discord
import logging
from fuzzy_match import Matcher

logger = logging.getLogger(__name__)


class EmbedContainer:
    def __init__(self, embed):
        self.embed = embed

    def get_embed(self):
        return self.embed


def create_queries(matcher: Matcher):
    add_query = matcher.add
    create_adventurer_queries(add_query)
    create_dragon_queries(add_query)
    create_wyrmprint_queries(add_query)
    create_weapon_queries(add_query)
    create_skill_queries(add_query)
    create_ability_queries(add_query)
    create_showcase_queries(add_query)


def get_name_map(entity_type: typing.Type[data.abc.Entity]):
    name_map = {str(e).lower(): e for e in entity_type.get_all().values()}
    entity_type_name = entity_type.__name__.lower()
    try:
        aliases = config.get_global(f"query_alias/{entity_type_name}")
    except FileNotFoundError:
        return name_map

    # add all aliases for this entity type
    for alias, expanded in aliases.items():
        try:
            resolved_entity = name_map[expanded]
        except KeyError:
            logger.warning(f"Alias '{alias}' = '{expanded}' doesn't resolve to any {entity_type_name}")
            continue

        if alias in name_map:
            logger.warning(f"Alias '{alias}' already exists as {entity_type_name} name")
        name_map[alias] = resolved_entity

    return name_map


def create_adventurer_queries(add_query: typing.Callable):
    adventurers = get_name_map(data.Adventurer)
    for name, a in adventurers.items():
        add_query(name, a)
        if a.skill_1:
            add_query(f"{name} s1", a.skill_1)
        if a.skill_2:
            add_query(f"{name} s2", a.skill_2)
        if a.ability_1:
            add_query(f"{name} a1", a.ability_1[-1])
        if a.ability_2:
            add_query(f"{name} a2", a.ability_2[-1])
        if a.ability_3:
            add_query(f"{name} a3", a.ability_3[-1])
        if a.coability:
            add_query(f"{name} coability", a.coability[-1])
            add_query(f"{name} coab", a.coability[-1])
        if a.chain_coability:
            cc = a.chain_coability[-1]
            add_query(f"{name} chain coability", cc)
            add_query(f"{name} chain coab", cc)
            add_query(f"{name} chain", cc)
            add_query(f"{name} cc", cc)


def create_dragon_queries(add_query: typing.Callable):
    dragons = get_name_map(data.Dragon)
    for name, d in dragons.items():
        add_query(name, d)
        if d.skill:
            add_query(f"{name} skill", d.skill)
            add_query(f"{name} s1", d.skill)
        if d.ability_1:
            add_query(f"{name} ability", d.ability_1[-1])
            add_query(f"{name} a1", d.ability_1[-1])
        if d.ability_2:
            add_query(f"{name} a2", d.ability_2[-1])


def create_wyrmprint_queries(add_query: typing.Callable):
    wyrmprints = get_name_map(data.Wyrmprint)
    for wp_name, wp in wyrmprints.items():
        names = [wp_name]
        name_words = wp_name.split(" ")
        if name_words[0] in ["a", "an", "the"]:
            names.append(" ".join(name_words[1:]))
        for name in names:
            add_query(name, wp)
            if wp.ability_1:
                add_query(f"{name} a1", wp.ability_1[-1])
            if wp.ability_2:
                add_query(f"{name} a2", wp.ability_2[-1])
            if wp.ability_3:
                add_query(f"{name} a3", wp.ability_3[-1])


def create_weapon_queries(add_query: typing.Callable):
    weapons = get_name_map(data.Weapon)
    for name, w in weapons.items():
        # determine descriptions for weapon
        descriptions = [name]
        if w.rarity and w.element and w.weapon_type:
            if w.availability == "Core":
                for element_name in w.element.get_names():
                    descriptions.append(f"{w.rarity}* {element_name} {w.weapon_type.name}")
            elif w.availability == "High Dragon" and w.tier:
                for element_name in w.element.get_names():
                    descriptions.append(f"d{w.tier} {element_name} {w.weapon_type.name}")
                    descriptions.append(f"h{w.tier} {element_name} {w.weapon_type.name}")
            elif w.availability == "Agito" and w.tier:
                for element_name in w.element.get_names():
                    descriptions.append(f"a{w.tier} {element_name} {w.weapon_type.name}")
                    if w.tier == 1:
                        descriptions.append(f"{w.rarity}* {element_name} {w.weapon_type.name}")
            elif w.name.startswith("Chimeratech") and w.tier:
                for element_name in w.element.get_names():
                    descriptions.append(f"ct{w.tier} {element_name} {w.weapon_type.name}")

        for desc in descriptions:
            add_query(desc, w)
            if w.skill:
                add_query(f"{desc} skill", w.skill)
                add_query(f"{desc} s1", w.skill)
            if w.ability_1:
                add_query(f"{desc} a1", w.ability_1)
            if w.ability_2:
                add_query(f"{desc} a2", w.ability_2)
            if w.obtained == "Crafting":
                add_query(f"{desc} cost", EmbedContainer(w.get_crafting_cost_embed()))


def create_skill_queries(add_query: typing.Callable):
    skills = get_name_map(data.Skill)
    for name, s in skills.items():
        add_query(name, s)


def create_ability_queries(add_query: typing.Callable):
    abilities = get_name_map(data.Ability)
    generic_ability_map = collections.defaultdict(list)
    for name, ab in abilities.items():
        # this will need to be addressed if different abilities have the same name
        add_query(name, ab, True)
        generic_ability_map[ab.generic_name].append(ab)

    generic_descriptions = config.get_global("ability_disambiguation")
    for name, ab_list in generic_ability_map.items():
        if len(ab_list) == 1:
            add_query(name, ab_list[0], True)
        else:
            if name in generic_descriptions:
                desc = f"*{generic_descriptions[name]}*"
            else:
                desc = ""
                logger.warning(f"No description for generic ability {name}")

            names = natsort.natsorted(set(ab.name for ab in ab_list))
            if len(names) > 15:
                names = names[:15] + ["..."]

            name_list = "\n".join(names)
            content = textwrap.dedent(f"""
                    {desc}

                    {name_list}
                    """)

            embed = discord.Embed(
                title=f"{name} (Disambiguation)",
                description=content.strip(),
                color=0xFF7000
            )

            add_query(name, EmbedContainer(embed))


def create_showcase_queries(add_query: typing.Callable):
    showcases = get_name_map(data.Showcase)
    replacements = {
        "part one": "part 1",
        "part two": "part 2",
    }
    for name, sh in showcases.items():
        add_query(name, sh)
        for old, new in replacements.items():
            if old in name:
                add_query(name.replace(old, new), sh)
