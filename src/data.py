import aiohttp
import util
import logging
import mwparserfromhell
import html
import re
import discord
import calendar
import collections
import urllib.parse
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
        logger.info("Updating wyrmprint repository")
        await Wyrmprint.update_repository(session)
        logger.info("Updating weapon repository")
        await Weapon.update_repository(session)
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


def get_rarity_colour(rarity):
    if 1 <= rarity <= 5:
        return [0xA39884, 0xA3E47A, 0xE29452, 0xCEE7FF, 0xFFCD26][rarity-1]
    return 0


def get_link(page_name):
    return "https://dragalialost.gamepedia.com/" + urllib.parse.quote(page_name.replace(" ", "_"))


class Element(MultiValueEnum):
    FIRE = 1, "Fire", "Flame"
    WATER = 2, "Water"
    WIND = 3, "Wind"
    LIGHT = 4, "Light"
    DARK = 5, "Dark", "Shadow"

    def __str__(self):
        return self.name.capitalize()

    def get_colour(self):
        return [0xE73031, 0x1790E0, 0x00D770, 0xFFBA10, 0xA738DE][self.value-1]


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
            adv.full_name = clean_wikitext(a["FullName"]) or None

            if adv.full_name is None:
                continue

            # basic info
            adv.name = clean_wikitext(a["Name"]) or None
            adv.title = clean_wikitext(a["Title"]) or None
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
            for slot in range(len(ability_slots)):
                for pos in range(4):
                    ability = Ability.abilities.get(clean_wikitext(a["Abilities{0}{1}".format(slot+1, pos+1)]))
                    ability_slots[slot] += filter(None, [ability])

            # add all coabilities that exist
            for pos in range(5):
                coability = CoAbility.coabilities.get(clean_wikitext(a["ExAbilityData{0}".format(pos + 1)]))
                adv.coability += filter(None, [coability])

            # add skills
            adv.skill_1 = Skill.skills.get(clean_wikitext(a["Skill1Name"]).lower())
            adv.skill_2 = Skill.skills.get(clean_wikitext(a["Skill2Name"]).lower())

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

    def __str__(self):
        return self.full_name

    def get_embed(self) -> discord.Embed:
        """
        Gets a discord embed representing this adventurer.
        :return: discord.Embed with information about the adventurer.
        """
        header_str = "{0}{1}{2} {3}: {4}".format(
            util.get_emote("rarity" + str(self.rarity)),
            util.get_emote(self.element or ""),
            util.get_emote(self.weapon_type or ""),
            self.name or "???",
            self.title or "???"
        )

        stats_str = "{0} HP  /  {1} Str  /  {2} Might\n\n".format(
            self.max_hp or "???",
            self.max_str or "???",
            self.max_might or "???"
        )

        skill_str = "**Skills**\n{0}\n{1}\n\n".format(
            "???" if (not self.skill_1 or not self.skill_1.name) else self.skill_1.name,
            "???" if (not self.skill_2 or not self.skill_2.name) else self.skill_2.name,
        )

        ability_str = "**Abilities**\n{0}\n{1}\n{2}\n\n".format(
            "???" if (not self.ability_1 or not self.ability_1[-1].name) else self.ability_1[-1].name,
            "???" if (not self.ability_2 or not self.ability_2[-1].name) else self.ability_2[-1].name,
            "???" if (not self.ability_3 or not self.ability_3[-1].name) else self.ability_3[-1].name
        )

        try:
            cab_min = self.coability[0].name or "???"
            cab_max = self.coability[-1].name or "???"
            coability_str = "**Co-ability:** {0}({1}-{2})%\n\n".format(
                cab_min[:cab_min.index("+") + 1],
                re.findall(r"(\d+)%", cab_min)[0],
                re.findall(r"(\d+)%", cab_max)[0]
            )
        except (IndexError, ValueError, TypeError):
            coability_str = "**Co-ability:** ???\n\n"

        footer_str = "*Obtained from:  {0}* \n*Release Date:  {1}* ".format(
            self.obtained or "???",
            self.release_date or "???"
        )

        desc = "".join((
            stats_str,
            skill_str,
            ability_str,
            coability_str,
            footer_str
        ))

        if self.element is not None:
            embed = discord.Embed(
                title=header_str,
                description=desc,
                url=get_link(self.full_name),
                colour=self.element.get_colour()
            )
        else:
            embed = discord.Embed(
                title=header_str,
                description=desc,
                url=get_link(self.full_name)
            )

        return embed


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
            dragon.full_name = clean_wikitext(d["FullName"]) or None

            if dragon.full_name is None:
                continue

            # basic info
            dragon.name = clean_wikitext(d["Name"]) or None
            dragon.title = clean_wikitext(d["Title"]) or None
            dragon.description = clean_wikitext(d["ProfileText"]) or None
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
            for slot in range(len(ability_slots)):
                for pos in range(2):
                    ability = Ability.abilities.get(clean_wikitext(d["Abilities{0}{1}".format(slot+1, pos+1)]))
                    ability_slots[slot] += filter(None, [ability])

            # add skill
            dragon.skill = Skill.skills.get(clean_wikitext(d["SkillName"]).lower())

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

    def __str__(self):
        return self.full_name

    def get_embed(self) -> discord.Embed:
        """
        Gets a discord embed representing this dragon.
        :return: discord.Embed with information about the dragon.
        """
        header_str = "{0}{1} {2}{3}".format(
            util.get_emote("rarity" + str(self.rarity)),
            util.get_emote(self.element or ""),
            self.name or "???",
            "" if not self.title else ": " + self.title
        )

        stats_str = "{0} HP  /  {1} Str  /  {2} Might\n\n".format(
            self.max_hp or "???",
            self.max_str or "???",
            self.max_might or "???"
        )

        skill_str = "**Skill:** {0}\n\n".format(
            "???" if (not self.skill or not self.skill.name) else self.skill.name,
        )

        ability_str = "**Abilities**\n" + (
            "???" if (not self.ability_1 or not self.ability_1[-1].name) else self.ability_1[-1].name)
        if self.ability_2 and self.ability_2[-1].name:
            ability_str += "\n" + self.ability_2[-1].name
        ability_str += "\n\n"

        footer_str = "*Favourite gift:  {0}* \n*Obtained from:  {1}* \n*Release Date:  {2}* ".format(
            "???" if not self.favourite_gift else "{0} ({1})".format(str(self.favourite_gift), calendar.day_name[
                self.favourite_gift.value - 1]),
            self.obtained or "???",
            self.release_date or "???"
        )

        desc = "".join((
            stats_str,
            skill_str,
            ability_str,
            footer_str
        ))

        if self.element is not None:
            embed = discord.Embed(
                title=header_str,
                description=desc,
                url=get_link(self.full_name),
                colour=self.element.get_colour()
            )
        else:
            embed = discord.Embed(
                title=header_str,
                description=desc,
                url=get_link(self.full_name)
            )

        return embed


class Wyrmprint:
    """
    Represents a wyrmprint and some of its associated data
    """
    wyrmprints = {}

    @classmethod
    async def update_repository(cls, session: aiohttp.ClientSession):
        base_url = "https://dragalialost.gamepedia.com/api.php?action=cargoquery&tables=Wyrmprints&format=json&limit=500&fields=" \
                   "Name,Rarity,MaxHp,MaxAtk,Obtain,DATE(ReleaseDate)%3DReleaseDate," \
                   "Abilities11,Abilities12," \
                   "Abilities21,Abilities22," \
                   "Abilities31,Abilities32" \
                   "&order_by=Name&offset="

        wyrmprint_info_list = await process_cargo_query(session, base_url)

        wyrmprints_new = {}

        safe_int = util.safe_int
        for wp in wyrmprint_info_list:
            wyrmprint = cls()
            wyrmprint.name = clean_wikitext(wp["Name"]) or None

            if wyrmprint.name is None:
                continue

            # basic info
            wyrmprint.rarity = safe_int(wp["Rarity"], None)
            wyrmprint.max_hp = safe_int(wp["MaxHp"], None)
            wyrmprint.max_str = safe_int(wp["MaxAtk"], None)
            wyrmprint.obtained = clean_wikitext(wp["Obtain"]) or None
            wyrmprint.release_date = wp["ReleaseDate"] if wp["ReleaseDate"] and not wp["ReleaseDate"].startswith("1970") else None

            # add all abilities that exist
            ability_slots = [wyrmprint.ability_1, wyrmprint.ability_2, wyrmprint.ability_3]
            for slot in range(len(ability_slots)):
                for pos in range(2):
                    ability = Ability.abilities.get(clean_wikitext(wp["Abilities{0}{1}".format(slot+1, pos+1)]))
                    ability_slots[slot] += filter(None, [ability])

            try:
                wyrmprint.max_might = wyrmprint.max_hp + wyrmprint.max_str + \
                                   (0 if not wyrmprint.ability_1 else wyrmprint.ability_1[-1].might) + \
                                   (0 if not wyrmprint.ability_2 else wyrmprint.ability_2[-1].might) + \
                                   (0 if not wyrmprint.ability_3 else wyrmprint.ability_3[-1].might)
            except (IndexError, TypeError):
                wyrmprint.max_might = None

            wyrmprints_new[wyrmprint.name.lower()] = wyrmprint

        cls.wyrmprints = wyrmprints_new

    def __init__(self):
        self.name = ""
        self.rarity = 0
        self.obtained = ""
        self.release_date = ""
        self.max_hp = 0
        self.max_str = 0
        self.max_might = 0

        self.ability_1 = []
        self.ability_2 = []
        self.ability_3 = []

    def __str__(self):
        return self.name

    def get_embed(self) -> discord.Embed:
        """
        Gets a discord embed representing this wyrmprint.
        :return: discord.Embed with information about the wyrmprint.
        """
        header_str = "{0} {1}".format(
            util.get_emote("rarity" + str(self.rarity)),
            self.name or "???",
        )

        stats_str = "{0} HP  /  {1} Str  /  {2} Might\n\n".format(
            self.max_hp or "???",
            self.max_str or "???",
            self.max_might or "???"
        )

        ability_str = "**Abilities**\n" + (
            "???" if (not self.ability_1 or not self.ability_1[-1].name) else self.ability_1[-1].name)
        if self.ability_2 and self.ability_2[-1].name:
            ability_str += "\n" + self.ability_2[-1].name
        if self.ability_3 and self.ability_3[-1].name:
            ability_str += "\n" + self.ability_3[-1].name
        ability_str += "\n\n"

        footer_str = "*Obtained from:  {0}* \n*Release Date:  {1}* ".format(
            self.obtained or "???",
            self.release_date or "???"
        )

        desc = "".join((
            stats_str,
            ability_str,
            footer_str
        ))

        if self.rarity is not None:
            embed = discord.Embed(
                title=header_str,
                description=desc,
                url=get_link(self.name),
                colour=get_rarity_colour(self.rarity)
            )
        else:
            embed = discord.Embed(
                title=header_str,
                description=desc,
                url=get_link(self.name)
            )

        return embed


class Weapon:
    """
    Represents a weapon and some of its associated data
    """
    weapons = {}

    @classmethod
    async def update_repository(cls, session: aiohttp.ClientSession):
        base_url = "https://dragalialost.gamepedia.com/api.php?action=cargoquery&tables=Weapons&format=json&limit=500&fields=" \
                   "WeaponName,Rarity,TypeId,ElementalTypeId,Obtain,MaxHp,MaxAtk," \
                   "SkillName,Abilities11,Abilities21," \
                   "CraftNodeId,ParentCraftNodeId,CraftGroupId" \
                   "&order_by=WeaponName&offset="

        weapon_info_list = await process_cargo_query(session, base_url)

        weapons_new = {}
        craft_groups = collections.defaultdict(lambda: collections.defaultdict(list))
        craft_index = {}

        safe_int = util.safe_int
        # initial pass for basic info
        for w in weapon_info_list:
            weapon = cls()
            weapon.name = clean_wikitext(w["WeaponName"]) or None

            if weapon.name is None:
                continue

            # basic info
            weapon.rarity = safe_int(w["Rarity"], None)
            wt_id = safe_int(w["TypeId"], None)
            weapon.weapon_type = None if wt_id is None else WeaponType(wt_id)
            el_id = safe_int(w["ElementalTypeId"], None)
            weapon.element = None if (el_id is None or el_id == 99) else Element(el_id)

            weapon.obtained = clean_wikitext(w["Obtain"]) or None
            weapon.max_hp = safe_int(w["MaxHp"], None)
            weapon.max_str = safe_int(w["MaxAtk"], None)

            # add all abilities that exist
            weapon.ability_1 = Ability.abilities.get(clean_wikitext(w["Abilities11"]))
            weapon.ability_2 = Ability.abilities.get(clean_wikitext(w["Abilities21"]))

            # add skill
            weapon.skill = Skill.skills.get(clean_wikitext(w["SkillName"]).lower())

            # max might adds 100 for skill if it exists
            try:
                weapon.max_might = weapon.max_hp + weapon.max_str + \
                                   (0 if not weapon.ability_1 else weapon.ability_1.might) + \
                                   (0 if not weapon.ability_2 else weapon.ability_2.might) + \
                                   (0 if not weapon.skill else 100)
            except (IndexError, TypeError):
                weapon.max_might = None

            # add to craft groups map for second pass
            group_id = clean_wikitext(w["CraftGroupId"])
            if group_id:
                node_id = clean_wikitext(w["CraftNodeId"])
                parent_node_id = clean_wikitext(w["ParentCraftNodeId"])
                craft_groups[group_id][parent_node_id].append(node_id)
                craft_index[group_id, node_id] = weapon

            weapons_new[weapon.name.lower()] = weapon

        # additional pass for crafting info

        for group_id, group in craft_groups.items():
            for parent_id, child_ids in group.items():
                parent = craft_index.get((group_id, parent_id))
                children = list(filter(None, (craft_index.get((group_id, ch_id)) for ch_id in child_ids)))
                if parent:
                    parent.crafted_to = children
                    for child in children:
                        child.crafted_from = parent

        cls.weapons = weapons_new

    def __init__(self):
        self.name = ""
        self.rarity = 0
        self.element = None
        self.weapon_type = None
        self.obtained = ""

        self.max_hp = 0
        self.max_str = 0
        self.max_might = 0

        self.skill = None
        self.ability_1 = None
        self.ability_2 = None

        self.crafted_from = None
        self.crafted_to = []

    def __str__(self):
        return self.name

    def get_title_string(self):
        w_tier = 0
        w_node = self
        while w_node is not None:
            w_node = w_node.crafted_from
            w_tier += 1

        return "{0}{1} {2} {3}{4}".format(
            util.get_emote("rarity" + str(self.rarity)),
            util.get_emote(("wtier" + str(w_tier)) if self.obtained == "Crafting" else ""),
            self.name or "???",
            util.get_emote(self.element or "none"),
            util.get_emote(self.weapon_type or "")
        )

    def get_embed(self) -> discord.Embed:
        """
        Gets a discord embed representing this weapon.
        :return: discord.Embed with information about the weapon.
        """

        header_str = self.get_title_string()

        stats_str = "{0} HP  /  {1} Str  /  {2} Might\n\n".format(
            self.max_hp or "???",
            self.max_str or "???",
            self.max_might or "???"
        )

        extra_str = ""
        if self.skill:
            extra_str += "**Skill:** {0}\n\n".format(
                "???" if (not self.skill or not self.skill.name) else self.skill.name,
            )

        if self.ability_1 or self.ability_2:
            extra_str += "**Abilities**\n" + (
                "???" if (not self.ability_1 or not self.ability_1.name) else self.ability_1.name)
            if self.ability_2 and self.ability_2.name:
                extra_str += "\n" + self.ability_2.name
            extra_str += "\n\n"

        if self.obtained == "Crafting":
            footer_str = ""
            if self.crafted_from is not None:
                footer_str += "{0}{0} **Crafted from**\n{1}\n\n".format(
                    util.get_emote("blank"),
                    self.crafted_from.get_title_string()
                )
            if len(self.crafted_to) > 0:
                footer_str += "{0}{0} **Used to craft**".format(util.get_emote("blank"))
                for child in self.crafted_to:
                    footer_str += "\n" + child.get_title_string()
            footer_str = footer_str.strip()
        else:
            footer_str = "*Obtained from:  {0}*".format(self.obtained or "???")

        desc = "".join((
            stats_str,
            extra_str,
            footer_str
        ))

        if self.element is not None:
            embed = discord.Embed(
                title=header_str,
                description=desc,
                url=get_link(self.name),
                colour=self.element.get_colour()
            )
        elif self.rarity is not None:
            embed = discord.Embed(
                title=header_str,
                description=desc,
                url=get_link(self.name),
                colour=get_rarity_colour(self.rarity)
            )
        else:
            embed = discord.Embed(
                title=header_str,
                description=desc,
                url=get_link(self.name),
            )

        return embed


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
            sk_name = clean_wikitext(s["Name"]) or None
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

            skills_new[sk.name.lower()] = sk

        cls.skills = skills_new

    def __init__(self, name: str):
        self.name = name
        self.levels = []

    def get_embed(self) -> discord.Embed:
        """
        Gets a discord embed representing the highest level of this skill.
        :return: discord.Embed with information about the skill.
        """
        skill_level = self.levels[-1]

        title_str = "{0} (Lv. {1} Skill)".format(self.name, len(self.levels))

        desc_str = "{0}\n\n**Cost: **{1} SP".format(
            skill_level.description or "???",
            str(skill_level.sp) or "???"
        )

        embed = discord.Embed(
            title=title_str,
            description=desc_str,
            url=get_link(self.name),
            color=get_rarity_colour(len(self.levels)+2)
        )

        return embed


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
            ab.name = clean_wikitext(a["Name"]) or None
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
            cab.name = clean_wikitext(c["Name"]) or None
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
