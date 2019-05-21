import calendar
import collections
import discord
import re
import util

from data import abc
from ._static import Element, WeaponType, DragonGift, get_rarity_colour


class Adventurer(abc.Entity):
    """
    Represents an adventurer and some of their associated data
    """

    repository: abc.EntityRepository = None

    @classmethod
    def get_all(cls):
        return cls.repository.data

    @classmethod
    def init(cls):
        mapper = abc.EntityMapper(Adventurer)
        cls.repository = abc.EntityRepository(mapper, "Adventurers")

        mp = mapper.add_property  # mapper property
        mf = abc.EntityMapper  # mapper functions

        mp("full_name", mf.text, "FullName")
        mp("name", mf.text, "Name")
        mp("title", mf.text, "Title")
        mp("description", mf.text, "Description")
        mp("obtained", mf.text, "Obtain")
        mp("release_date", mf.date, "ReleaseDate")
        mp("weapon_type", WeaponType.get, "WeaponTypeId")
        mp("element", Element.get, "ElementalTypeId")
        mp("rarity", mf.int, "Rarity")
        mp("max_hp", mf.sum, "MaxHp", "PlusHp0", "PlusHp1", "PlusHp2", "PlusHp3", "PlusHp4", "McFullBonusHp5")
        mp("max_str", mf.sum, "MaxAtk", "PlusAtk0", "PlusAtk1", "PlusAtk2", "PlusAtk3", "PlusAtk4", "McFullBonusAtk5")
        mp("ability_1", mf.filtered_list_of(Ability.find), *("Abilities1{0}".format(i + 1) for i in range(4)))
        mp("ability_2", mf.filtered_list_of(Ability.find), *("Abilities2{0}".format(i + 1) for i in range(4)))
        mp("ability_3", mf.filtered_list_of(Ability.find), *("Abilities3{0}".format(i + 1) for i in range(4)))
        mp("coability", mf.filtered_list_of(CoAbility.find), *("ExAbilityData{0}".format(i + 1) for i in range(5)))
        mp("skill_1", Skill.find, "Skill1Name")
        mp("skill_2", Skill.find, "Skill2Name")

        def post_processor(adv: Adventurer):
            try:
                # max might adds 500 for all max level skills, 120 for force strike level 2
                adv.max_might = adv.max_hp + adv.max_str + 500 + 120 + \
                                adv.ability_1[-1].might + adv.ability_2[-1].might + adv.ability_3[-1].might + \
                                adv.coability[-1].might
            except (IndexError, TypeError):
                adv.max_might = None

            return True

        mapper.post_processor = post_processor

    def __init__(self):
        self.full_name = ""
        self.name = ""
        self.title = ""
        self.description = ""
        self.obtained = ""
        self.release_date = None
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

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key.lower())

    def get_key(self):
        return self.full_name.lower()

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
            self.release_date.date().isoformat() if self.release_date else "???"
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
                url=util.get_link(self.full_name),
                colour=self.element.get_colour()
            )
        else:
            embed = discord.Embed(
                title=header_str,
                description=desc,
                url=util.get_link(self.full_name)
            )

        return embed


class Dragon(abc.Entity):
    """
    Represents a dragon and some of their associated data
    """

    repository: abc.EntityRepository = None

    @classmethod
    def get_all(cls):
        return cls.repository.data

    @classmethod
    def init(cls):
        mapper = abc.EntityMapper(Dragon)
        cls.repository = abc.EntityRepository(mapper, "Dragons")

        mp = mapper.add_property  # mapper property
        mf = abc.EntityMapper  # mapper functions
        mp("full_name", mf.text, "FullName")
        mp("name", mf.text, "Name")
        mp("title", mf.text, "Title")
        mp("description", mf.text, "ProfileText")
        mp("obtained", mf.text, "Obtain")
        mp("release_date", mf.date, "ReleaseDate")
        mp("rarity", mf.int, "Rarity")
        mp("element", Element.get, "ElementalTypeId")
        mp("max_hp", mf.int, "MaxHp")
        mp("max_str", mf.int, "MaxAtk")
        mp("favourite_gift", DragonGift.get, "FavoriteType")

        mp("ability_1", mf.filtered_list_of(Ability.find), *("Abilities1{0}".format(i + 1) for i in range(2)))
        mp("ability_2", mf.filtered_list_of(Ability.find), *("Abilities2{0}".format(i + 1) for i in range(2)))
        mp("skill", Skill.find, "SkillName")

        def post_processor(dragon: Dragon):
            try:
                # max might adds 300 for bond 30, 100 for skill 1
                dragon.max_might = dragon.max_hp + dragon.max_str + 300 + 100 + \
                                   (0 if not dragon.ability_1 else dragon.ability_1[-1].might) + \
                                   (0 if not dragon.ability_2 else dragon.ability_2[-1].might)
            except (IndexError, TypeError):
                dragon.max_might = None

            return True

        mapper.post_processor = post_processor

    def __init__(self):
        self.full_name = ""
        self.name = ""
        self.title = ""
        self.description = ""
        self.obtained = ""
        self.release_date = None
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

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key.lower())

    def get_key(self):
        return self.full_name.lower()

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
            self.release_date.date().isoformat() if self.release_date else "???"
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
                url=util.get_link(self.full_name),
                colour=self.element.get_colour()
            )
        else:
            embed = discord.Embed(
                title=header_str,
                description=desc,
                url=util.get_link(self.full_name)
            )

        return embed


class Wyrmprint(abc.Entity):
    """
    Represents a wyrmprint and some of its associated data
    """

    repository: abc.EntityRepository = None

    @classmethod
    def get_all(cls):
        return cls.repository.data

    @classmethod
    def init(cls):
        mapper = abc.EntityMapper(Wyrmprint)
        cls.repository = abc.EntityRepository(mapper, "Wyrmprints")

        mp = mapper.add_property  # mapper property
        mf = abc.EntityMapper  # mapping functions

        mp("name", mf.text, "Name")
        mp("rarity", mf.int, "Rarity")
        mp("max_hp", mf.int, "MaxHp")
        mp("max_str", mf.int, "MaxAtk")
        mp("obtained", lambda s: re.split("\n+", mf.text(s)) if mf.text(s) else None, "Obtain")
        mp("release_date", mf.date, "ReleaseDate")

        mp("ability_1", mf.filtered_list_of(Ability.find), *("Abilities1{0}".format(i + 1) for i in range(3)))
        mp("ability_2", mf.filtered_list_of(Ability.find), *("Abilities2{0}".format(i + 1) for i in range(3)))
        mp("ability_3", mf.filtered_list_of(Ability.find), *("Abilities3{0}".format(i + 1) for i in range(3)))

        def post_processor(wp: Wyrmprint):
            try:
                wp.max_might = wp.max_hp + wp.max_str + \
                               (0 if not wp.ability_1 else wp.ability_1[-1].might) + \
                               (0 if not wp.ability_2 else wp.ability_2[-1].might) + \
                               (0 if not wp.ability_3 else wp.ability_3[-1].might)
            except (IndexError, TypeError):
                wp.max_might = None

            return True

        mapper.post_processor = post_processor

    def __init__(self):
        self.name = ""
        self.rarity = 0
        self.obtained = []
        self.release_date = None
        self.max_hp = 0
        self.max_str = 0
        self.max_might = 0

        self.ability_1 = []
        self.ability_2 = []
        self.ability_3 = []

    def __str__(self):
        return self.name

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key.lower())

    def get_key(self):
        return self.name.lower()

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

        footer_str = "**Obtained from**\n{0}\n\n*Release Date:  {1}* ".format(
            "\n".join(self.obtained) if self.obtained else "???",
            self.release_date.date().isoformat() if self.release_date else "???"
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
                url=util.get_link(self.name),
                colour=get_rarity_colour(self.rarity)
            )
        else:
            embed = discord.Embed(
                title=header_str,
                description=desc,
                url=util.get_link(self.name)
            )

        return embed


class Weapon(abc.Entity):
    """
    Represents a weapon and some of its associated data
    """
    repository: abc.EntityRepository = None

    @classmethod
    def get_all(cls):
        return cls.repository.data

    @classmethod
    def init(cls):
        mapper = abc.EntityMapper(Weapon)
        cls.repository = abc.EntityRepository(mapper, "Weapons")

        mp = mapper.add_property  # mapper property
        mf = abc.EntityMapper  # mapper functions

        mp("name", mf.text, "WeaponName")
        mp("rarity", mf.int, "Rarity")
        mp("weapon_type", WeaponType.get, "TypeId")
        mp("element", Element.get, "ElementalTypeId")
        mp("obtained", mf.text, "Obtain")
        mp("max_hp", mf.int, "MaxHp")
        mp("max_str", mf.int, "MaxAtk")

        mp("ability_1", Ability.find, "Abilities11")
        mp("ability_2", Ability.find, "Abilities21")
        mp("skill", Skill.find, "SkillName")

        mp(None, mf.none, "CraftGroupId", "CraftNodeId", "ParentCraftNodeId")

        def mapper_post_processor(weapon: Weapon):
            # max might adds 100 for skill if it exists
            try:
                weapon.max_might = weapon.max_hp + weapon.max_str + \
                                   (0 if not weapon.ability_1 else weapon.ability_1.might) + \
                                   (0 if not weapon.ability_2 else weapon.ability_2.might) + \
                                   (0 if not weapon.skill else 100)
            except (IndexError, TypeError):
                weapon.max_might = None

            return True

        def repo_post_processor(weapons: dict):
            craft_groups = collections.defaultdict(lambda: collections.defaultdict(list))
            craft_index = {}

            for w in weapons.values():
                # add to craft groups map for second pass
                pp = w.POST_PROCESS
                group_id = mf.text(pp["CraftGroupId"])
                if group_id:
                    node_id = mf.text(pp["CraftNodeId"])
                    parent_node_id = mf.text(pp["ParentCraftNodeId"])
                    craft_groups[group_id][parent_node_id].append(node_id)
                    craft_index[group_id, node_id] = w
                delattr(w, "POST_PROCESS")

            # no need to use passed in weapons
            for group_id, group in craft_groups.items():
                for parent_id, child_ids in group.items():
                    parent = craft_index.get((group_id, parent_id))
                    children = list(filter(None, (craft_index.get((group_id, ch_id)) for ch_id in child_ids)))
                    if parent:
                        parent.crafted_to = children
                        for child in children:
                            child.crafted_from = parent

        mapper.post_processor = mapper_post_processor
        cls.repository.post_processor = repo_post_processor

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

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key.lower())

    def get_key(self):
        return self.name.lower()

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
                url=util.get_link(self.name),
                colour=self.element.get_colour()
            )
        elif self.rarity is not None:
            embed = discord.Embed(
                title=header_str,
                description=desc,
                url=util.get_link(self.name),
                colour=get_rarity_colour(self.rarity)
            )
        else:
            embed = discord.Embed(
                title=header_str,
                description=desc,
                url=util.get_link(self.name),
            )

        return embed

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


class Skill(abc.Entity):
    """
    Represents a skill and some of its associated data
    """
    repository: abc.EntityRepository = None

    class SkillLevel:
        def __init__(self, desc: str, sp: int):
            self.description = desc
            self.sp = sp

        def __repr__(self):
            return str(vars(self))

    @classmethod
    def get_all(cls):
        return cls.repository.data

    @classmethod
    def init(cls):
        mapper = abc.EntityMapper(Skill)
        cls.repository = abc.EntityRepository(mapper, "Skills")

        mp = mapper.add_property  # mapper property
        mf = abc.EntityMapper  # mapper functions

        def skill_levels(*args):
            s1 = Skill.SkillLevel(mf.text(args[0]), mf.int(args[3]))
            s2 = Skill.SkillLevel(mf.text(args[1]), mf.int(args[4]))
            s3 = Skill.SkillLevel(mf.text(args[2]), mf.int(args[5]))

            if args[6] != "1":
                return [s1, s2, s3]

            return [s1, s2]

        mp("name", mf.text, "Name")
        mp("levels", skill_levels, "Description1", "Description2", "Description3", "Sp", "SPLv2", "SPLv2", "HideLevel3")

    def __init__(self):
        self.name = ""
        self.levels = []

    def __str__(self):
        return self.name

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key.lower())

    def get_key(self):
        return self.name.lower()

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
            url=util.get_link(self.name),
            color=get_rarity_colour(len(self.levels) + 2)
        )

        return embed


class Ability(abc.Entity):
    """
    Represents an ability and some of its associated data
    """

    repository: abc.EntityRepository = None

    @classmethod
    def get_all(cls):
        return cls.repository.data

    @classmethod
    def init(cls):
        def generic_name(s: str):
            text = mf.text(s)
            if not text:
                return None

            return re.sub(r"\([^)]+\)", "", text).strip() or None

        mapper = abc.EntityMapper(Ability)
        cls.repository = abc.EntityRepository(mapper, "Abilities")

        mp = mapper.add_property  # mapper property
        mf = abc.EntityMapper  # mapper functions

        mp("id_str", mf.text, "Id")
        mp("name", mf.text, "Name")
        mp("generic_name", generic_name, "GenericName")
        mp("description", mf.text, "Details")
        mp("might", mf.int, "PartyPowerWeight")

    def __init__(self):
        self.id_str = ""
        self.name = ""
        self.generic_name = ""
        self.description = ""
        self.might = 0

    def __str__(self):
        return self.name

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key)

    def get_key(self):
        return self.id_str

    def get_embed(self) -> discord.Embed:
        return discord.Embed()


class CoAbility(abc.Entity):
    """
    Represents a co-ability and some of its associated data
    """

    repository: abc.EntityRepository = None

    @classmethod
    def get_all(cls):
        return cls.repository.data

    @classmethod
    def init(cls):
        mapper = abc.EntityMapper(CoAbility)
        cls.repository = abc.EntityRepository(mapper, "CoAbilities")

        mp = mapper.add_property  # mapper property
        mf = abc.EntityMapper  # mapper functions

        mp("id_str", mf.text, "Id")
        mp("name", mf.text, "Name")
        mp("generic_name", mf.text, "GenericName")
        mp("description", mf.text, "Details")
        mp("might", mf.int, "PartyPowerWeight")

    def __init__(self):
        self.id_str = ""
        self.name = ""
        self.generic_name = ""
        self.description = ""
        self.might = 0

    def __str__(self):
        return self.name

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key)

    def get_key(self):
        return self.id_str

    def get_embed(self) -> discord.Embed:
        return discord.Embed()


Adventurer.init()
Dragon.init()
Wyrmprint.init()
Weapon.init()
Skill.init()
Ability.init()
CoAbility.init()
