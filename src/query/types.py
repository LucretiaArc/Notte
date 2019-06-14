import enum

import data


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


class FlagSkill:
    pass


class FlagAbility:
    pass


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

    # boolean flags
    FLAG_SKILL = FlagSkill
    FLAG_ABILITY = FlagAbility
