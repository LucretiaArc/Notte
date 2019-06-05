import data
import enum
import hook
import logging
import acora
import itertools
import operator

logger = logging.getLogger(__name__)

client = None
keyword_finder = None


# New keyword types
class Rarity(enum.Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5


class SkillSlot(enum.Enum):
    SKILL_1 = 1
    SKILL_2 = 2


class AbilitySlot(enum.Enum):
    ABILITY_1 = 1
    ABILITY_2 = 2
    ABILITY_3 = 3


class Tier(enum.Enum):
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3
    TIER_4 = 4
    TIER_5 = 5


class AbilityGeneric:
    def __init__(self, name):
        self.name = name
        self.values = []


class Type(enum.Enum):
    """
    Represents a keyword type.
    """
    # entities
    ADVENTURER = data.Adventurer
    DRAGON = data.Dragon
    WYRMPRINT = data.Wyrmprint
    SKILL = data.Skill

    # properties
    RARITY = Rarity
    ELEMENT = data.Element
    WEAPON_TYPE = data.WeaponType
    TIER = Tier

    # slots
    SKILL_SLOT = SkillSlot
    ABILITY_SLOT = AbilitySlot

    # other
    ABILITY_GENERIC = AbilityGeneric


class KeywordFinder:
    def __init__(self):
        self.keywords = {}
        self.builder = acora.AcoraBuilder()
        self.finder = self.builder.build()

    def add(self, key: str, *values):
        if key in self.keywords:
            raise ValueError(f"Keyword {key} already exists")

        for v in values:
            try:
                Type(type(v))
            except ValueError:
                logger.exception("Value's type must be one of Type")

        self.keywords[key.lower()] = values
        self.builder.add(key.lower())

    def rebuild(self):
        # initialise builder
        self.finder = self.builder.build()

    def match(self, input_string):
        # gets longest matches for keywords (non-overlapping)
        matches = []
        last_pos = 0
        for pos, match_set in itertools.groupby(self.finder.finditer(input_string), operator.itemgetter(1)):
            filtered_matches = list(filter(lambda m: m[1] >= last_pos, match_set))
            if filtered_matches:
                next_match = max(filtered_matches)
                matches.append(next_match[0])
                last_pos = next_match[1] + len(next_match[0])

        return sorted(
            itertools.chain(*(self.keywords[key] for key in matches)),
            key=lambda x: type(x).__name__
        )


def add_keywords(finder: KeywordFinder):
        # rarity
        for i in range(1, 6):
            finder.add(f"{i}*", Rarity(i))

        # element
        for e in data.Element:
            for v in e.values[1:]:
                finder.add(v, e)

        # weapon type
        for w in data.WeaponType:
            finder.add(w.name, w)

        # tier
        for i in range(1, 6):
            finder.add(f"t{i}", Tier(i))

        # skill slots
        for i in range(1, 3):
            finder.add(f"s{i}", SkillSlot(i))

        # ability slots
        for i in range(1, 4):
            finder.add(f"a{i}", AbilitySlot(i))

        # weapon crafting classes
        for rarity in range(3, 6):
            for tier in range(1, 4):
                finder.add(f"{rarity}t{tier}", Rarity(rarity), Tier(tier))

        # ability generics
        generics = {}
        abilities = data.Ability.get_all().values()
        for a in abilities:
            if a.generic_name not in generics:
                generics[a.generic_name] = AbilityGeneric(a.generic_name)

            generics[a.generic_name].values.append(a.get_key())

        for k, v in generics.items():
            finder.add(k, v)

        # repositories
        entity_repositories = [
            data.Adventurer.get_all(),
            data.Dragon.get_all(),
            data.Wyrmprint.get_all(),
            data.Skill.get_all()
        ]
        for r in entity_repositories:
            for k, v in r.items():
                finder.add(k, v)

        # rebuild to ensure the keywords match properly
        finder.rebuild()


async def on_init(discord_client):
    global client, keyword_finder
    client = discord_client

    keyword_finder = KeywordFinder()
    add_keywords(keyword_finder)


async def query(message, args):
    """
    Performs a query on the provided terms.
    """
    pass


hook.Hook.get("on_init").attach(on_init)
