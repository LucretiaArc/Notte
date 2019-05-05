import util
import enum
import aenum


class Element(aenum.MultiValueEnum):
    FIRE = 1, "Fire", "Flame"
    WATER = 2, "Water"
    WIND = 3, "Wind"
    LIGHT = 4, "Light"
    DARK = 5, "Dark", "Shadow"

    @staticmethod
    def get(s: str):
        element_id = util.safe_int(s, None)
        return None if element_id not in range(1, 6) else Element(element_id)

    def __str__(self):
        return self.name.capitalize()

    def __repr__(self):
        return "Element.{0}".format(self.name)

    def get_colour(self):
        return [0xE73031, 0x1790E0, 0x00D770, 0xFFBA10, 0xA738DE][self.value-1]


class WeaponType(enum.Enum):
    SWORD = 1
    BLADE = 2
    DAGGER = 3
    AXE = 4
    LANCE = 5
    BOW = 6
    WAND = 7
    STAFF = 8

    @staticmethod
    def get(s: str):
        type_id = util.safe_int(s, None)
        return None if type_id not in range(1, 9) else WeaponType(type_id)

    def __str__(self):
        return self.name.capitalize()

    def __repr__(self):
        return "WeaponType.{0}".format(self.name)


class Resistance(aenum.MultiValueEnum):
    POISON = "Poison"
    BURN = "Burn", "Burning"
    FREEZE = "Freeze", "Freezing"
    PARALYSIS = "Paralysis"
    BLIND = "Blind", "Blindness"
    STUN = "Stun"
    CURSE = "Curse", "Curses"
    BOG = "Bog"
    SLEEP = "Sleep"

    def __str__(self):
        return self.name.capitalize()

    def __repr__(self):
        return "Resistance.{0}".format(self.name)


class DragonGift(aenum.MultiValueEnum):
    JUICY_MEAT = 1
    KALEIDOSCOPE = 2
    FLORAL_CIRCLET = 3
    COMPELLING_BOOK = 4
    MANA_ESSENCE = 5
    GOLDEN_CHALICE = 6, 7

    @staticmethod
    def get(s: str):
        gift_id = util.safe_int(s, None)
        return None if gift_id not in range(1, 8) else DragonGift(gift_id)

    def __str__(self):
        return self.name.replace("_", " ").title()

    def __repr__(self):
        return "DragonGift.{0}".format(self.name)


def get_rarity_colour(rarity):
    if 1 <= rarity <= 5:
        return [0xA39884, 0xA3E47A, 0xE29452, 0xCEE7FF, 0xFFCD26][rarity-1]
    return 0
