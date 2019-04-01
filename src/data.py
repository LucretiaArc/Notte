import aiohttp
import util
import logging
import mwparserfromhell
import html
import re
from enum import Enum
from aenum import MultiValueEnum
from hook import Hook

logger = logging.getLogger(__name__)


async def update_repositories():
    async with aiohttp.ClientSession() as session:
        logger.info("Updating skill repository")
        await Skill.update_repository(session)
        logger.info("Updating ability repository")
        await Ability.update_repository(session)
        logger.info("Updating coability repository")
        await CoAbility.update_repository(session)
        logger.info("Updating adventurer repository")
        await Adventurer.update_repository(session)
        logger.info("Updating dragon repository")
        await Dragon.update_repository(session)
        logger.info("Updated all repositories.")


def clean_wikitext(wikitext):
    """
    Applies several transformations to wikitext, so that it's suitable for display in a message. This function does NOT
    sanitise the input, so the output of this method isn't safe for use in a HTML document. This method, in no
    particular order:
     - Strips spaces from the ends
     - Strips wikicode
     - Decodes HTML entities then strips HTML tags
     - Reduces consecutive spaces
    :param wikitext: wikitext to strip
    :return: string representing the stripped wikitext
    """
    html_removed = re.sub(r"(<[^<]+?>)", "", html.unescape(wikitext))
    wikicode_removed = mwparserfromhell.parse(html_removed).strip_code()
    spaces_reduced = re.sub(r" {2,}", " ", wikicode_removed)
    return spaces_reduced.strip()


async def process_cargo_query(session: aiohttp.ClientSession, base_url: str, limit=500):
    """
    Retrieves the results for a json cargo query, which may be split across multiple queries due to a result limit. The
    query MUST sort the results unambiguously to ensure the results are properly retrieved.
    :param session: aiohttp.ClientSession to use for the requests
    :param base_url: base url to use for the query, with the end of the string open to append an offset (e.g. ending in
    "&offset=")
    :param limit: result limit for each request
    :return: list of result entries
    """

    offset = 0
    result_items = []
    while True:
        async with session.get(base_url + str(offset)) as response:
            result_json = await response.json()
            inner_result_list = result_json["cargoquery"]
            query_items = [d["title"] for d in inner_result_list]
            result_items += query_items
            offset += limit

            if len(query_items) < limit or len(inner_result_list) == 0:
                return result_items


class Element(MultiValueEnum):
    FIRE = 1, "Fire", "Flame"
    WATER = 2, "Water"
    WIND = 3, "Wind"
    LIGHT = 4, "Light"
    DARK = 5, "Dark", "Shadow"

    def __str__(self):
        return self.name.capitalize()


class WeaponType(Enum):
    SWORD = 1
    BLADE = 2
    DAGGER = 3
    AXE = 4
    LANCE = 5
    BOW = 6
    WAND = 7
    STAFF = 8

    def __str__(self):
        return self.name.capitalize()


class Resistance(MultiValueEnum):
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


class DragonGift(MultiValueEnum):
    JUICY_MEAT = 1
    KALEIDOSCOPE = 2
    FLORAL_CIRCLET = 3
    COMPELLING_BOOK = 4
    MANA_ESSENCE = 5
    GOLDEN_CHALICE = 6, 7

    def __str__(self):
        return self.name.replace("_", " ").title()


class Adventurer:
    """
    Represents an adventurer and some of their associated data
    """
    adventurers = {}

    @classmethod
    async def update_repository(cls, session: aiohttp.ClientSession):
        base_url = "https://dragalialost.gamepedia.com/api.php?action=cargoquery&tables=Adventurers&format=json&limit=500&fields=" \
                   "Id,FullName,Name,Title,Description,Obtain,DATE(ReleaseDate)%3DReleaseDate," \
                   "WeaponTypeId,ElementalTypeId,Rarity," \
                   "MaxHp,PlusHp0,PlusHp1,PlusHp2,PlusHp3,PlusHp4,McFullBonusHp5," \
                   "MaxAtk,PlusAtk0,PlusAtk1,PlusAtk2,PlusAtk3,PlusAtk4,McFullBonusAtk5," \
                   "Skill1Name,Skill2Name," \
                   "Abilities11,Abilities12,Abilities13,Abilities14," \
                   "Abilities21,Abilities22,Abilities23,Abilities24," \
                   "Abilities31,Abilities32,Abilities33,Abilities34," \
                   "ExAbilityData1,ExAbilityData2,ExAbilityData3,ExAbilityData4,ExAbilityData5" \
                   "&order_by=Id&offset="

        adventurer_info_list = await process_cargo_query(session, base_url)

        adventurers_new = {}

        safe_int = util.safe_int
        for a in adventurer_info_list:
            adv = cls()
            adv.full_name = a["FullName"] or None

            if adv.full_name is None:
                continue

            # basic info
            adv.name = a["Name"] or None
            adv.title = a["Title"] or None
            adv.description = clean_wikitext(a["Description"]) or None
            adv.obtained = clean_wikitext(a["Obtain"]) or None
            adv.release_date = a["ReleaseDate"] if a["ReleaseDate"] and not a["ReleaseDate"].startswith("1970") else None
            wt_id = safe_int(a["WeaponTypeId"], None)
            adv.weapon_type = None if wt_id is None else WeaponType(wt_id)
            el_id = safe_int(a["ElementalTypeId"], None)
            adv.element = None if el_id is None else Element(el_id)
            adv.rarity = safe_int(a["Rarity"], None)

            # max hp calculation
            max_hp_vals = [
                safe_int(a["MaxHp"], None),
                safe_int(a["PlusHp0"], None),
                safe_int(a["PlusHp1"], None),
                safe_int(a["PlusHp2"], None),
                safe_int(a["PlusHp3"], None),
                safe_int(a["PlusHp4"], None),
                safe_int(a["McFullBonusHp5"], None),
            ]
            try:
                adv.max_hp = sum(max_hp_vals)
            except TypeError:
                adv.max_hp = None

            # max strength calculation
            max_str_vals = [
                safe_int(a["MaxAtk"], None),
                safe_int(a["PlusAtk0"], None),
                safe_int(a["PlusAtk1"], None),
                safe_int(a["PlusAtk2"], None),
                safe_int(a["PlusAtk3"], None),
                safe_int(a["PlusAtk4"], None),
                safe_int(a["McFullBonusAtk5"], None),
            ]
            try:
                adv.max_str = sum(max_str_vals)
            except TypeError:
                adv.max_str = None

            # add all abilities that exist
            ability_slots = [adv.ability_1, adv.ability_2, adv.ability_3]
            for slot in range(3):
                for pos in range(4):
                    ability = Ability.abilities.get(a["Abilities{0}{1}".format(slot+1, pos+1)])
                    ability_slots[slot] += filter(None, [ability])

            # add all coabilities that exist
            for pos in range(5):
                coability = CoAbility.coabilities.get(a["ExAbilityData{0}".format(pos + 1)])
                adv.coability += filter(None, [coability])

            # add skills
            adv.skill_1 = Skill.skills.get(a["Skill1Name"].strip())
            adv.skill_2 = Skill.skills.get(a["Skill2Name"].strip())

            # max might adds 500 for all max level skills, 120 for force strike level 2
            try:
                adv.max_might = adv.max_hp + adv.max_str + 500 + 120 + \
                    adv.ability_1[-1].might + \
                    adv.ability_2[-1].might + \
                    adv.ability_3[-1].might + \
                    adv.coability[-1].might
            except (IndexError, TypeError):
                adv.max_might = None

            adventurers_new[adv.full_name.lower()] = adv

        cls.adventurers = adventurers_new

    def __init__(self):
        self.full_name = ""
        self.name = ""
        self.title = ""
        self.description = ""
        self.obtained = ""
        self.release_date = ""
        self.weapon_type = None
        self.rarity = 0
        self.element = None
        self.max_hp = 0
        self.max_str = 0
        self.max_might = 0

        self.skill_1 = None
        self.skill_2 = None
        self.ability_1 = []
        self.ability_2 = []
        self.ability_3 = []
        self.coability = []

    def dump(self):
        dump_dict = vars(self)
        dump_dict["weapon_type"] = str(dump_dict["weapon_type"])
        dump_dict["element"] = str(dump_dict["element"])
        dump_dict["skill_1"] = vars(dump_dict["skill_1"])
        dump_dict["skill_1"]["levels"] = [vars(d) for d in dump_dict["skill_1"]["levels"]]
        dump_dict["skill_2"] = vars(dump_dict["skill_2"])
        dump_dict["skill_2"]["levels"] = [vars(d) for d in dump_dict["skill_2"]["levels"]]
        dump_dict["ability_1"] = [vars(d) for d in dump_dict["ability_1"]]
        dump_dict["ability_2"] = [vars(d) for d in dump_dict["ability_2"]]
        dump_dict["ability_3"] = [vars(d) for d in dump_dict["ability_3"]]
        dump_dict["coability"] = [vars(d) for d in dump_dict["coability"]]
        return dump_dict


class Dragon:
    """
    Represents a dragon and some of their associated data
    """
    dragons = {}

    @classmethod
    async def update_repository(cls, session: aiohttp.ClientSession):
        base_url = "https://dragalialost.gamepedia.com/api.php?action=cargoquery&tables=Dragons&format=json&limit=500&fields=" \
                   "FullName,Name,Title,ProfileText,MaxHp,MaxAtk,Rarity,ElementalTypeId," \
                   "FavoriteType,Obtain,DATE(ReleaseDate)%3DReleaseDate," \
                   "SkillName,Abilities11,Abilities12,Abilities21,Abilities22" \
                   "&order_by=FullName&offset="

        dragon_info_list = await process_cargo_query(session, base_url)

        dragons_new = {}

        safe_int = util.safe_int
        for d in dragon_info_list:
            dragon = cls()
            dragon.full_name = d["FullName"] or None

            if dragon.full_name is None:
                continue

            # basic info
            dragon.name = d["Name"] or None
            dragon.title = d["Title"] or None
            dragon.description = d["ProfileText"] or None
            dragon.obtained = clean_wikitext(d["Obtain"]) or None
            dragon.release_date = d["ReleaseDate"] if d["ReleaseDate"] and not d["ReleaseDate"].startswith("1970") else None
            dragon.rarity = safe_int(d["Rarity"], None)
            dragon.max_hp = safe_int(d["MaxHp"], None)
            dragon.max_str = safe_int(d["MaxAtk"], None)
            el_id = safe_int(d["ElementalTypeId"], None)
            dragon.element = None if el_id is None else Element(el_id)
            gift_id = safe_int(d["FavoriteType"], None)
            dragon.favourite_gift = None if gift_id is None else DragonGift(gift_id)

            # add all abilities that exist
            ability_slots = [dragon.ability_1, dragon.ability_2]
            for slot in range(2):
                for pos in range(2):
                    ability = Ability.abilities.get(d["Abilities{0}{1}".format(slot+1, pos+1)])
                    ability_slots[slot] += filter(None, [ability])

            # add skill
            dragon.skill = Skill.skills.get(d["SkillName"].strip())

            # max might adds 300 for bond 30, 100 for skill 1
            try:
                dragon.max_might = dragon.max_hp + dragon.max_str + 300 + 100 + \
                                   (0 if not dragon.ability_1 else dragon.ability_1[-1].might) + \
                                   (0 if not dragon.ability_2 else dragon.ability_2[-1].might)
            except (IndexError, TypeError):
                dragon.max_might = None

            dragons_new[dragon.full_name.lower()] = dragon

        cls.dragons = dragons_new

    def __init__(self):
        self.full_name = ""
        self.name = ""
        self.title = ""
        self.description = ""
        self.obtained = ""
        self.release_date = ""
        self.rarity = 0
        self.element = None
        self.max_hp = 0
        self.max_str = 0
        self.max_might = 0
        self.favourite_gift = None

        self.skill = None
        self.ability_1 = []
        self.ability_2 = []

    def dump(self):
        dump_dict = vars(self)
        dump_dict["element"] = str(dump_dict["element"])
        dump_dict["favourite_gift"] = str(dump_dict["favourite_gift"])
        if dump_dict["skill"] is not None:
            dump_dict["skill"] = vars(dump_dict["skill"])
            dump_dict["skill"]["levels"] = [vars(d) for d in dump_dict["skill"]["levels"]]
        dump_dict["ability_1"] = [vars(d) for d in dump_dict["ability_1"]]
        dump_dict["ability_2"] = [vars(d) for d in dump_dict["ability_2"]]
        return dump_dict


class Skill:
    """
    Represents a skill and some of its associated data
    """
    skills = {}

    @classmethod
    async def update_repository(cls, session: aiohttp.ClientSession):
        base_url = "https://dragalialost.gamepedia.com/api.php?action=cargoquery&tables=Skills&format=json&limit=500&fields=" \
                   "SkillId,Name,Description1,Description2,Description3,HideLevel3,Sp,SPLv2" \
                   "&order_by=SkillId&offset="

        skill_info_list = await process_cargo_query(session, base_url)

        skills_new = {}

        safe_int = util.safe_int
        for s in skill_info_list:
            sk_name = s["Name"] or None
            if sk_name is None:
                continue

            sk = cls(sk_name)

            s1 = SkillLevel(
                clean_wikitext(s["Description1"]) or None,
                safe_int(s["Sp"], None)
            )

            s2 = SkillLevel(
                clean_wikitext(s["Description2"]) or None,
                safe_int(s["SPLv2"], None)
            )

            s3 = SkillLevel(
                clean_wikitext(s["Description3"]) or None,
                safe_int(s["SPLv2"], None)
            )

            sk.levels = [s1, s2]
            if s["HideLevel3"] != "1":
                sk.levels.append(s3)

            skills_new[sk.name] = sk

        cls.skills = skills_new

    def __init__(self, name: str):
        self.name = name
        self.levels = []


class SkillLevel:
    def __init__(self, desc: str, sp: int):
        self.description = desc
        self.sp = sp


class Ability:
    """
    Represents an ability and some of its associated data
    """
    abilities = {}

    @classmethod
    async def update_repository(cls, session: aiohttp.ClientSession):
        base_url = "https://dragalialost.gamepedia.com/api.php?action=cargoquery&tables=Abilities&format=json&limit=500&fields=" \
                   "Id,Name,Details,PartyPowerWeight" \
                   "&order_by=Id&offset="

        ability_info_list = await process_cargo_query(session, base_url)

        abilities_new = {}

        safe_int = util.safe_int
        for a in ability_info_list:
            ab_id = a["Id"] or None
            if ab_id is None:
                continue

            ab = cls(ab_id)
            ab.name = a["Name"] or None
            ab.description = clean_wikitext(a["Details"]) or None
            ab.might = safe_int(a["PartyPowerWeight"], None)

            abilities_new[ab_id] = ab

        cls.abilities = abilities_new

    def __init__(self, id_str: str):
        self.id_str = id_str
        self.name = ""
        self.description = ""
        self.might = 0


class CoAbility:
    """
    Represents a co-ability and some of its associated data
    """
    coabilities = {}

    @classmethod
    async def update_repository(cls, session: aiohttp.ClientSession):
        base_url = "https://dragalialost.gamepedia.com/api.php?action=cargoquery&tables=CoAbilities&format=json&limit=500&fields=" \
                   "Id,Name,Details,PartyPowerWeight" \
                   "&order_by=Id&offset="

        coability_info_list = await process_cargo_query(session, base_url)

        coabilities_new = {}

        safe_int = util.safe_int
        for c in coability_info_list:
            cab_id = c["Id"] or None
            if cab_id is None:
                continue

            cab = cls(cab_id)
            cab.name = c["Name"] or None
            cab.description = clean_wikitext(c["Details"]) or None
            cab.might = safe_int(c["PartyPowerWeight"], None)

            coabilities_new[cab_id] = cab

        cls.coabilities = coabilities_new

    def __init__(self, id_str: str):
        self.id_str = id_str
        self.name = ""
        self.description = ""
        self.might = 0


Hook.get("download_data").attach(update_repositories)
