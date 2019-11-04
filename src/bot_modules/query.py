import re
import discord
import urllib.parse
import data
import hook
import logging
import jellyfish
import jellyfish._jellyfish as py_jellyfish
import pybktree
import config
import util
import typing

logger = logging.getLogger(__name__)

client = None
resolver: "QueryResolver" = None
query_config = None


class QueryResolver:
    def __init__(self):
        self.query_tree = pybktree.BKTree(QueryResolver.calculate_edit_distance)
        self.query_map = {}
        self.max_query_len = 0

    @staticmethod
    def calculate_edit_distance(a, b):
        try:
            return jellyfish.damerau_levenshtein_distance(a, b)
        except ValueError:
            return py_jellyfish.damerau_levenshtein_distance(a, b)

    @staticmethod
    def get_match_threshold(input_string: str):
        return 1 + 0.3 * len(input_string)

    def add(self, target: str, result):
        """
        Adds a string as a resolution target, with a result object to map to it.
        :param target: target string to map to result object
        :param result: object to map, may not be None
        """
        target_str = target.lower()
        if target_str in self.query_map:
            logger.warning(f'Query string "{target_str}" already exists, ignoring new addition')
            return
        elif result is None:
            raise ValueError(f"Result may not be None")

        self.query_map[target_str] = result
        self.query_tree.add(target_str)
        self.max_query_len = max(self.max_query_len, len(target_str))

    def match(self, query_string: str):
        """
        Return all match keys for a query string
        :param query_string: string to match
        :return: all results, as a list of tuples (edit distance, result key)
        """
        match_threshold = QueryResolver.get_match_threshold(query_string)
        return self.query_tree.find(query_string.lower(), match_threshold)

    def resolve(self, query_string: str):
        """
        Resolves and returns the closest match to a query
        :param query_string: query string to resolve
        :return a tuple of (result object, match key, match distance as a fraction of threshold) if a match is found,
        else None
        """
        results = self.match(query_string)
        if not results:
            return None
        else:
            match_distance, match_key = results[0]
            match_threshold = QueryResolver.get_match_threshold(query_string)
            return self.query_map[match_key], match_key, 1 - match_distance / match_threshold


async def on_init(discord_client):
    global client, resolver, query_config
    client = discord_client
    resolver = QueryResolver()
    query_config = config.get_global("custom_query")

    initialise_keywords(resolver)

    hook.Hook.get("on_message").attach(scan_for_query)
    hook.Hook.get("owner!query_results").attach(resolve_keywords)
    hook.Hook.get("data_downloaded").attach(rebuild_resolver)


async def scan_for_query(message):
    if "[" in message.content:
        matches = re.findall(r"\[\[(.+?)\]\]", message.content.lower())
        if len(matches) > 0:
            if len(matches) > 3:
                await message.channel.send("Too many queries, only the first three will be shown.")

            is_special_guild = message.guild and message.guild.id in query_config["special_guilds"]
            for raw_match in matches[:3]:
                if len(raw_match) > resolver.max_query_len + 5:
                    await message.channel.send("That's way too much, I'm not looking for that!")
                    continue

                response = resolve_query(raw_match, is_special_guild)
                if isinstance(response, str):
                    await message.channel.send(response)
                elif isinstance(response, discord.Embed):
                    await message.channel.send(embed=response)


def resolve_query(query: str, include_special_responses=False):
    special_query_messages = query_config["special_query_messages"]
    regular_query_messages = query_config["query_messages"]
    search_term = query.lower()
    embed = None

    # resolve custom query messages
    title, content = None, None
    if search_term in special_query_messages and include_special_responses:
        title = special_query_messages[search_term][0]
        content = special_query_messages[search_term][1]
    elif search_term in regular_query_messages:
        title = regular_query_messages[search_term][0]
        content = regular_query_messages[search_term][1]

    if title and content:
        # construct embed for custom message
        if urllib.parse.urlparse(content).scheme:
            embed = discord.Embed(title=title).set_image(url=content)
        else:
            embed = discord.Embed(title=title, description=content)
    else:
        # query the resolver
        match_content = resolver.resolve(search_term)
        if match_content:
            embed = match_content[0].copy()
            if match_content[2] < 0.7:
                embed.set_footer(text=f'Displaying result for "{match_content[1]}"')

    return embed or f"I'm not sure what \"{query}\" is."


def initialise_keywords(query_resolver: QueryResolver):
    original_capacity = len(query_resolver.query_map)
    add_query = query_resolver.add

    adventurers: typing.Dict[str, data.Adventurer] = data.Adventurer.get_all().copy()
    dragons: typing.Dict[str, data.Dragon] = data.Dragon.get_all().copy()
    wyrmprints: typing.Dict[str, data.Wyrmprint] = data.Wyrmprint.get_all().copy()
    skills: typing.Dict[str, data.Skill] = data.Skill.get_all().copy()
    weapons: typing.Dict[str, data.Weapon] = data.Weapon.get_all().copy()

    local_data_maps = {
        "adventurer": adventurers,
        "dragon": dragons,
        "wyrmprint": wyrmprints,
        "skill": skills,
    }

    logger.info("Resolving query shortcuts")

    for entity_type, local_map in local_data_maps.items():
        try:
            aliases = config.get_global(f"query_alias/{entity_type}")
        except FileNotFoundError:
            continue

        # add all entity shortcuts for this type
        for shortcut, expanded in aliases.items():
            try:
                resolved_entity = local_map[expanded]
            except KeyError:
                logger.warning(f"Shortcut '{shortcut}' = '{expanded}' doesn't resolve to any {entity_type}")
                continue

            if shortcut in local_map:
                logger.warning(f"Shortcut '{shortcut}'' resolves to {entity_type} multiple times")
            local_map[shortcut] = resolved_entity

    logger.info("Query shortcuts resolved.")
    logger.info("Generating queries")

    for name, a in adventurers.items():
        add_query(name, a.get_embed())
        if a.skill_1:
            add_query(f"{name} s1", a.skill_1.get_embed())
        if a.skill_2:
            add_query(f"{name} s2", a.skill_2.get_embed())
        if a.ability_1:
            add_query(f"{name} a1", a.ability_1[-1].get_embed())
        if a.ability_2:
            add_query(f"{name} a2", a.ability_2[-1].get_embed())
        if a.ability_3:
            add_query(f"{name} a3", a.ability_3[-1].get_embed())
        if a.coability:
            add_query(f"{name} coability", a.coability[-1].get_embed())
            add_query(f"{name} coab", a.coability[-1].get_embed())

    for name, d in dragons.items():
        add_query(name, d.get_embed())
        if d.skill:
            add_query(f"{name} skill", d.skill.get_embed())
            add_query(f"{name} s1", d.skill.get_embed())
        if d.ability_1:
            add_query(f"{name} ability", d.ability_1[-1].get_embed())
            add_query(f"{name} a1", d.ability_1[-1].get_embed())
        if d.ability_2:
            add_query(f"{name} a2", d.ability_2[-1].get_embed())

    for name, wp in wyrmprints.items():
        add_query(name, wp.get_embed())
        if wp.ability_1:
            add_query(f"{name} a1", wp.ability_1[-1].get_embed())
        if wp.ability_2:
            add_query(f"{name} a2", wp.ability_2[-1].get_embed())
        if wp.ability_3:
            add_query(f"{name} a3", wp.ability_3[-1].get_embed())

    for name, s in skills.items():
        add_query(name, s.get_embed())

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

        for desc in descriptions:
            add_query(desc, w.get_embed())
            if w.skill:
                add_query(f"{desc} skill", w.skill.get_embed())
                add_query(f"{desc} s1", w.skill.get_embed())
            if w.ability_1:
                add_query(f"{desc} a1", w.ability_1.get_embed())
            if w.ability_2:
                add_query(f"{desc} a2", w.ability_2.get_embed())
            if w.obtained == "Crafting":
                add_query(f"{desc} cost", w.get_crafting_cost_embed())

    logger.info(f"{len(query_resolver.query_map) - original_capacity} queries generated and added to resolver.")
    logger.info(f"Determined maximum query length {query_resolver.max_query_len}")


def rebuild_resolver():
    global resolver
    logger.info("Rebuilding query resolver...")
    new_resolver = QueryResolver()
    initialise_keywords(new_resolver)
    resolver = new_resolver
    logger.info("Query resolver rebuilt.")


async def resolve_keywords(message, args):
    max_dist = QueryResolver.get_match_threshold(args)
    await message.channel.send(
        util.readable_list([f'"{key}" ({int(100 * (1 - dist / max_dist))}%)' for dist, key in resolver.match(args)])
        or "No results found."
    )


hook.Hook.get("on_init").attach(on_init)
