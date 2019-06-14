import data
import hook
import logging
import acora
import itertools
import operator
import inspect
import asyncio
import discord
import query.types as qt
import query.handlers as handlers

logger = logging.getLogger(__name__)

client = None
keyword_resolver: "KeywordResolver" = None
query_resolver: "QueryResolver" = None


class KeywordResolver:
    def __init__(self):
        self.keywords = {}
        self.builder = acora.AcoraBuilder()
        self.finder = self.builder.build()

    def add(self, key: str, *values):
        if key in self.keywords:
            raise ValueError(f"Keyword {key} already exists")

        for v in values:
            try:
                qt.Type(type(v))
            except ValueError:
                logger.exception("Value's type must be one of Type")

        self.keywords[key.lower()] = values
        self.builder.add(key.lower())

    def rebuild(self):
        self.finder = self.builder.build()

    def match(self, input_string):
        matches = []
        last_keyword_end_pos = 0
        for pos, match_set in itertools.groupby(self.finder.finditer(input_string), operator.itemgetter(1)):
            if pos < last_keyword_end_pos:
                continue

            keyword = max(match_set)[0]
            matches.append(keyword)
            last_keyword_end_pos = pos + len(keyword)

        # sorts and resolves keywords to their values
        return sorted(
            itertools.chain(*(self.keywords[key] for key in matches)),
            key=lambda x: type(x).__name__
        )


class QueryResolver:
    def __init__(self):
        self.functions = {}  # stores a tuple (function, sorted argument position)

    @staticmethod
    def get_arg_signature(*args):
        return tuple(sorted(args, key=lambda t: t.__name__))

    def register(self, function, *args: qt.Type):
        """
        Registers a function to respond to a set of arguments.
        :param function: Function to register. Returns a discord.Embed or string to send as a response, or None if an
        error occurred.
        :param args: arguments to be provided to the function, in the order they are to be provided.
        """
        arg_types = [arg.value for arg in args]
        arg_signature = QueryResolver.get_arg_signature(*arg_types)

        if arg_signature in self.functions:
            raise ValueError(f"Argument signature already exists: {arg_signature}")

        order = [x[0] for x in sorted(zip(range(len(arg_types)), arg_types), key=lambda x: x[1].__name__)]
        self.functions[arg_signature] = (function, order)

    async def resolve(self, *args):
        """
        Resolves and executes a function for the provided arguments.
        :param args: arguments to be operated on.
        :return: the return value of the executed function, or None if the arguments did not resolve to a function.
        The return value of the executed function should be a discord.Embed or string as a response to the query.
        """
        arg_types = [type(arg) for arg in args]
        arg_signature = QueryResolver.get_arg_signature(*arg_types)
        function_details = self.functions.get(arg_signature)

        if function_details:
            # successfully resolved
            function, order = function_details
            ordered_args = [x[0] for x in sorted(zip(args, order), key=operator.itemgetter(1))]
            if inspect.iscoroutinefunction(function):
                return await asyncio.ensure_future(function(*ordered_args))
            else:
                return function(*ordered_args)
        else:
            # did not resolve
            return None


def add_keywords(resolver: KeywordResolver):
        # rarity
        for i in range(1, 6):
            resolver.add(f"{i}*", qt.Rarity(i))

        # element
        for e in data.Element:
            for v in e.values[1:]:
                resolver.add(v, e)

        # weapon type
        for w in data.WeaponType:
            resolver.add(w.name, w)

        # tier
        for i in range(1, 6):
            resolver.add(f"t{i}", qt.Tier(i))

        # skill slots
        for i in range(1, 3):
            resolver.add(f"s{i}", qt.SkillSlot(i))

        # ability slots
        for i in range(1, 4):
            resolver.add(f"a{i}", qt.AbilitySlot(i))

        # weapon crafting classes
        for rarity in range(3, 6):
            for tier in range(1, 4):
                resolver.add(f"{rarity}t{tier}", qt.Rarity(rarity), qt.Tier(tier))

        # repositories
        entity_repositories = [
            data.Adventurer.get_all(),
            data.Dragon.get_all(),
            data.Wyrmprint.get_all(),
            data.Skill.get_all()
        ]
        for r in entity_repositories:
            for k, v in r.items():
                resolver.add(k, v)

        # flags
        resolver.add("skill", qt.FlagSkill())
        resolver.add("ability", qt.FlagAbility())

        # rebuild to ensure the keywords match properly
        resolver.rebuild()


async def on_init(discord_client):
    global client, keyword_resolver, query_resolver
    client = discord_client
    keyword_resolver = KeywordResolver()
    query_resolver = QueryResolver()

    add_keywords(keyword_resolver)
    query_resolver.register(handlers.get_adventurer_skill, qt.Type.ADVENTURER, qt.Type.SKILL_SLOT)
    query_resolver.register(handlers.get_tierless_weapon, qt.Type.RARITY, qt.Type.WEAPON_TYPE)
    query_resolver.register(handlers.get_t1_weapon, qt.Type.RARITY, qt.Type.TIER, qt.Type.WEAPON_TYPE)
    query_resolver.register(handlers.get_t2_t3_weapon, qt.Type.RARITY, qt.Type.TIER, qt.Type.WEAPON_TYPE, qt.Type.ELEMENT)

    hook.Hook.get("public!query").attach(query)
    hook.Hook.get("owner!query_keywords").attach(resolve_keywords)


async def resolve_keywords(message, args):
    await message.channel.send(str([type(arg_type).__name__ for arg_type in keyword_resolver.match(args)]))


async def query(message, args):
    """
    Performs a query on the provided terms.
    """
    func_args = keyword_resolver.match(args)
    response = await query_resolver.resolve(*func_args)
    if isinstance(response, str):
        await message.channel.send(response)
    elif isinstance(response, discord.Embed):
        await message.channel.send(embed=response)
    else:
        await message.channel.send("I'm not sure what you want exactly, sorry!")


hook.Hook.get("on_init").attach(on_init)
