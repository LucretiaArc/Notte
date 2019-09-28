import calendar
import collections
import discord
import re
import util
import textwrap
import datetime
import typing
import logging
from data import abc
from ._static import Element, WeaponType, DragonGift, get_rarity_colour

logger = logging.getLogger(__name__)


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
        mp("ability_1", mf.filtered_list_of(Ability.find), *(f"Abilities1{i+1}" for i in range(4)))
        mp("ability_2", mf.filtered_list_of(Ability.find), *(f"Abilities2{i+1}" for i in range(4)))
        mp("ability_3", mf.filtered_list_of(Ability.find), *(f"Abilities3{i+1}" for i in range(4)))
        mp("coability", mf.filtered_list_of(CoAbility.find), *(f"ExAbilityData{i+1}" for i in range(5)))
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

            for sk in [adv.skill_1, adv.skill_2]:
                if sk:
                    if sk.owner:
                        logger.warning(f"Skill {sk.name} already has owner")
                    else:
                        sk.owner = adv

            return True

        mapper.post_processor = post_processor

    def __init__(self):
        self.full_name = ""
        self.name = ""
        self.title = ""
        self.description = ""
        self.obtained = ""
        self.release_date: datetime.datetime = None
        self.weapon_type: WeaponType = None
        self.rarity = 0
        self.element: Element = None
        self.max_hp = 0
        self.max_str = 0
        self.max_might = 0

        self.skill_1: Skill = None
        self.skill_2: Skill = None
        self.ability_1: typing.List[Ability] = []
        self.ability_2: typing.List[Ability] = []
        self.ability_3: typing.List[Ability] = []
        self.coability: typing.List[CoAbility] = []

    def __str__(self):
        return self.full_name

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key.lower())

    def get_key(self):
        if self.full_name:
            return self.full_name.lower()
        else:
            return None

    def get_embed(self) -> discord.Embed:
        fmt = abc.EmbedFormatter()

        try:
            cab_min = self.coability[0].name or "???"
            cab_max = self.coability[-1].name or "???"
            coability_str = "{0}({1}-{2})%".format(
                cab_min[:cab_min.index("+") + 1],
                re.findall(r"(\d+)%", cab_min)[0],
                re.findall(r"(\d+)%", cab_max)[0]
            )
        except (IndexError, ValueError, TypeError):
            coability_str = "?"

        title = fmt.format("{e.rarity!r}{e.element!e}{e.weapon_type!e} {e.name}: {e.title}", e=self)
        description = fmt.format(
            textwrap.dedent("""
                {e.max_hp} HP / {e.max_str} Str / {e.max_might} Might
                
                **Skills**
                {e.skill_1.name}
                {e.skill_2.name}
                
                **Abilities**
                {e.ability_1[-1].name}
                {e.ability_2[-1].name}
                {e.ability_3[-1].name}
                
                **Co-ability:** {coability}
                
                *Obtained from: {e.obtained}*
                *Release Date: {e.release_date!d}* 
                """),
            e=self,
            coability=coability_str
        )

        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.full_name),
            colour=discord.Embed.Empty if not self.element else self.element.get_colour()
        )


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

        mp("ability_1", mf.filtered_list_of(Ability.find), *(f"Abilities1{i+1}" for i in range(2)))
        mp("ability_2", mf.filtered_list_of(Ability.find), *(f"Abilities2{i+1}" for i in range(2)))
        mp("skill", Skill.find, "SkillName")

        def post_processor(dragon: Dragon):
            try:
                # max might adds 300 for bond 30, 100 for skill 1
                dragon.max_might = dragon.max_hp + dragon.max_str + 300 + 100 + \
                                   (0 if not dragon.ability_1 else dragon.ability_1[-1].might) + \
                                   (0 if not dragon.ability_2 else dragon.ability_2[-1].might)
            except (IndexError, TypeError):
                dragon.max_might = None

            if dragon.skill:
                if dragon.skill.owner:
                    logger.warning(f"Skill {dragon.skill.name} already has owner")
                else:
                    dragon.skill.owner = dragon

            return True

        mapper.post_processor = post_processor

    def __init__(self):
        self.full_name = ""
        self.name = ""
        self.title = ""
        self.description = ""
        self.obtained = ""
        self.release_date: datetime.datetime = None
        self.rarity = 0
        self.element: Element = None
        self.max_hp = 0
        self.max_str = 0
        self.max_might = 0
        self.favourite_gift: DragonGift = None

        self.skill: Skill = None
        self.ability_1: typing.List[Ability] = []
        self.ability_2: typing.List[Ability] = []

    def __str__(self):
        return self.full_name

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key.lower())

    def get_key(self):
        if self.full_name:
            return self.full_name.lower()
        else:
            return None

    def get_embed(self) -> discord.Embed:
        fmt = abc.EmbedFormatter()

        title = fmt.format(
            "{e.rarity!r}{e.element!e} {e.name}{title}",
            e=self,
            title=(": " + self.title) if self.title else " "
        )

        description = fmt.format(
            textwrap.dedent("""
                {e.max_hp} HP / {e.max_str} Str / {e.max_might} Might 

                **Skill:** {e.skill.name} 

                **Abilities** 
                {e.ability_1[-1].name}{e.ability_2[-1].name!o} 
                
                *Favourite gift: {gift}* 
                *Obtained from: {e.obtained}* 
                *Release Date: {e.release_date!d}* 
                """),
            e=self,
            gift="" if not self.favourite_gift else "{0} ({1})".format(
                str(self.favourite_gift),
                calendar.day_name[self.favourite_gift.value - 1]
            )
        )

        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.full_name),
            colour=discord.Embed.Empty if not self.element else self.element.get_colour()
        )


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
        mp("obtained", lambda s: re.split("[,\n]+", mf.text(s)) if mf.text(s) else None, "Obtain")
        mp("release_date", mf.date, "ReleaseDate")

        mp("ability_1", mf.filtered_list_of(Ability.find), *(f"Abilities1{i+1}" for i in range(3)))
        mp("ability_2", mf.filtered_list_of(Ability.find), *(f"Abilities2{i+1}" for i in range(3)))
        mp("ability_3", mf.filtered_list_of(Ability.find), *(f"Abilities3{i+1}" for i in range(3)))

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
        self.release_date: datetime.datetime = None
        self.max_hp = 0
        self.max_str = 0
        self.max_might = 0

        self.ability_1: typing.List[Ability] = []
        self.ability_2: typing.List[Ability] = []
        self.ability_3: typing.List[Ability] = []

    def __str__(self):
        return self.name

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key.lower())

    def get_key(self):
        if self.name:
            return self.name.lower()
        else:
            return None

    def get_embed(self) -> discord.Embed:
        fmt = abc.EmbedFormatter()

        title = fmt.format("{e.rarity!r} {e.name}", e=self)

        description = fmt.format(
            textwrap.dedent("""
                {e.max_hp} HP / {e.max_str} Str / {e.max_might} Might 

                **Abilities** 
                {e.ability_1[-1].name}{e.ability_2[-1].name!o} {e.ability_3[-1].name!o} 
                
                **Obtained from**
                {obtain} 
                  
                *Release Date: {e.release_date!d}* 
                """),
            e=self,
            obtain="\n".join(self.obtained) if self.obtained else ""
        )

        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.name),
            colour=get_rarity_colour(self.rarity)
        )


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
        mp("availability", mf.text, "Availability")

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

            if weapon.skill:
                if weapon.skill.owner:
                    logger.warning(f"Skill {weapon.skill.name} already has owner")
                else:
                    weapon.skill.owner = weapon

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

            # set weapon tiers
            for w in weapons.values():
                if w.obtained == "Crafting":
                    w.tier = 0
                    w_node = w
                    while w_node is not None:
                        w_node = w_node.crafted_from
                        w.tier += 1

        mapper.post_processor = mapper_post_processor
        cls.repository.post_processor = repo_post_processor

    def __init__(self):
        self.name = ""
        self.rarity = 0
        self.element: Element = None
        self.weapon_type: WeaponType = None
        self.obtained = ""
        self.availability = ""

        self.max_hp = 0
        self.max_str = 0
        self.max_might = 0

        self.skill: Skill = None
        self.ability_1: Ability = None
        self.ability_2: Ability = None

        self.crafted_from: Weapon = None
        self.crafted_to: typing.List[Weapon] = []
        self.tier: int = None

    def __str__(self):
        return self.name

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key.lower())

    def get_key(self):
        if self.name:
            return self.name.lower()
        else:
            return None

    def get_embed(self) -> discord.Embed:
        fmt = abc.EmbedFormatter()

        sections = []

        # skill
        if self.skill:
            sections.append(fmt.format("**Skill:** {e.skill.name} ", e=self))

        # abilities
        if self.ability_1 or self.ability_2:
            sections.append(fmt.format("**Abilities**\n{e.ability_1.name}{e.ability_2.name!o} ", e=self))

        # obtained from
        if self.obtained == "Crafting":
            if self.crafted_from:
                sections.append(fmt.format(
                    "{0!e}{0!e} **Crafted from**\n{1} ",
                    "blank",
                    self.crafted_from.get_title_string()
                ))

            if self.crafted_to:
                sections.append(fmt.format(
                    "{0!e}{0!e} **Used to craft**\n{1} ",
                    "blank",
                    "\n".join(child.get_title_string() for child in self.crafted_to)
                ))
        else:
            sections.append(fmt.format("*Obtained from: {e.obtained}* ", e=self))

        description = fmt.format(
            textwrap.dedent("""
                {e.max_hp} HP / {e.max_str} Str / {e.max_might} Might 

                {sections}
                """),
            e=self,
            sections="\n\n".join(sections)
        )

        if self.element is not None:
            colour = self.element.get_colour()
        elif self.rarity is not None:
            colour = get_rarity_colour(self.rarity)
        else:
            colour = discord.Embed.Empty

        return discord.Embed(
            title=self.get_title_string(),
            description=description,
            url=util.get_link(self.name),
            colour=colour
        )

    def get_title_string(self):
        w_tier = 0
        w_node = self
        while w_node is not None:
            w_node = w_node.crafted_from
            w_tier += 1

        return abc.EmbedFormatter().format(
            "{e.rarity!r}{tier!e} {e.name} {e.element!e}{e.weapon_type!e}",
            e=self,
            tier=("wtier" + str(w_tier)) if self.obtained == "Crafting" else ""
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
        self.levels: typing.List[Skill.SkillLevel] = []
        self.owner: abc.Entity = None  # needs to be updated manually

    def __str__(self):
        return self.name

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key.lower())

    def get_key(self):
        if self.name:
            return self.name.lower()
        else:
            return None

    def get_embed(self) -> discord.Embed:
        fmt = abc.EmbedFormatter()

        title = fmt.format("{e.name} (Lv. {e.levels!l} Skill)", e=self)
        description = fmt.format(
            textwrap.dedent("""
                {max_level.description}

                **Cost:** {max_level.sp} SP
                **Used by:** {e.owner}
                """),
            e=self,
            max_level=self.levels[-1] if self.levels else Skill.SkillLevel("", 0)
        )

        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.name),
            color=get_rarity_colour(len(self.levels) + 2)
        )


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
        fmt = abc.EmbedFormatter()

        title = fmt.format("{e.name} (Ability)", e=self)
        description = fmt.format(
            textwrap.dedent("""
                {e.description}

                **Might:** {e.might}
                """),
            e=self
        )

        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.name),
            color=0xFF7000
        )


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
        fmt = abc.EmbedFormatter()

        title = fmt.format("{e.name} (Co-Ability)", e=self)
        description = fmt.format(
            textwrap.dedent("""
                {e.description}

                **Might:** {e.might}
                """),
            e=self
        )

        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.generic_name),
            color=0x006080
        )


Adventurer.init()
Dragon.init()
Wyrmprint.init()
Weapon.init()
Skill.init()
Ability.init()
CoAbility.init()
