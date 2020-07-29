import collections
import itertools
import discord
import re
import util
import datetime
import logging
from typing import List, Optional
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
        return cls.repository.data.values()

    @classmethod
    def init(cls):
        mapper = abc.EntityMapper(Adventurer)
        cls.repository = abc.EntityRepository(mapper, "Adventurers")

        mp = mapper.add_property  # mapper property
        mf = abc.EntityMapper  # mapper functions

        def max_stat(max_limit_break, max_50, max_70, mc_50_bonus, *plus_hp):
            if mf.int0(max_limit_break) >= 5:
                return mf.int0(max_70) + mf.int0(mc_50_bonus) + sum(map(mf.int0, plus_hp))
            else:
                return mf.int0(max_50) + mf.int0(mc_50_bonus) + sum(map(mf.int0, plus_hp[:5]))

        mp("full_name", mf.text, "FullName")
        mp("name", mf.text, "Name")
        mp("title", mf.text, "Title")
        mp("description", mf.text, "Description")
        mp("obtained", mf.text, "Obtain")
        mp("availability", mf.text, "Availability")
        mp("release_date", mf.date, "ReleaseDate")
        mp("weapon_type", WeaponType.get, "WeaponTypeId")
        mp("element", Element.get, "ElementalTypeId")
        mp("rarity", mf.int, "Rarity")
        mp("max_hp", max_stat, "MaxLimitBreakCount", "MaxHp", "AddMaxHp1", "McFullBonusHp5", "PlusHp0", "PlusHp1", "PlusHp2", "PlusHp3", "PlusHp4", "PlusHp5")
        mp("max_str", max_stat, "MaxLimitBreakCount", "MaxAtk", "AddMaxAtk1", "McFullBonusAtk5", "PlusAtk0", "PlusAtk1", "PlusAtk2", "PlusAtk3", "PlusAtk4", "PlusAtk5")
        mp("max_nodes", lambda n: 70 if mf.int0(n) >= 5 else 50, "MaxLimitBreakCount")
        mp("ability_1", mf.filtered_list_of(Ability.find), *(f"Abilities1{i + 1}" for i in range(4)))
        mp("ability_2", mf.filtered_list_of(Ability.find), *(f"Abilities2{i + 1}" for i in range(4)))
        mp("ability_3", mf.filtered_list_of(Ability.find), *(f"Abilities3{i + 1}" for i in range(4)))
        mp("coability", mf.filtered_list_of(CoAbility.find), *(f"ExAbilityData{i + 1}" for i in range(5)))
        mp("chain_coability", mf.filtered_list_of(ChainCoAbility.find), *(f"ExAbility2Data{i + 1}" for i in range(5)))
        mp("skill_1", Skill.find, "Skill1ID")
        mp("skill_2", Skill.find, "Skill2ID")
        mp("icon_name", lambda i, v, r: f"{i}_0{v}_r0{r}", "Id", "VariationId", "Rarity")
        mp("is_playable", mf.bool, "IsPlayable")

        mapper.set_post_process_args("EditSkillId", "EditSkillCost")

        def post_processor(adv: Adventurer):
            try:
                adv.max_might = sum((
                    adv.max_hp,
                    adv.max_str,
                    100 * len(adv.skill_1.levels),
                    100 * len(adv.skill_2.levels),
                    adv.ability_1[-1].might,
                    adv.ability_2[-1].might,
                    adv.ability_3[-1].might,
                    adv.coability[-1].might,
                    120,  # force strike level 2
                    200 if adv.max_nodes > 50 else 0  # standard attack level 2
                ))
            except (IndexError, TypeError, AttributeError):
                adv.max_might = None

            pp = getattr(adv, "_POST_PROCESS")
            delattr(adv, "_POST_PROCESS")
            shared_skill_id = pp["EditSkillId"]
            for sk in [adv.skill_1, adv.skill_2]:
                if sk:
                    sk.owner.append(adv)
                    if sk.id == shared_skill_id:
                        sk.share_cost = mf.int0(pp["EditSkillCost"])

            return True

        mapper.post_processor = post_processor

    def __init__(self):
        self.full_name = ""
        self.name = ""
        self.title = ""
        self.description = ""
        self.obtained = ""
        self.availability = ""
        self.release_date: Optional[datetime.datetime] = None
        self.weapon_type: Optional[WeaponType] = None
        self.rarity = 0
        self.element: Optional[Element] = None
        self.max_hp = 0
        self.max_str = 0
        self.max_might = 0
        self.max_nodes = 0
        self.icon_name = ""
        self.skill_1: Optional[Skill] = None
        self.skill_2: Optional[Skill] = None
        self.ability_1: List[Ability] = []
        self.ability_2: List[Ability] = []
        self.ability_3: List[Ability] = []
        self.coability: List[CoAbility] = []
        self.chain_coability: List[ChainCoAbility] = []
        self.is_playable = True

    def __str__(self):
        return self.full_name

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key.lower())

    def get_key(self):
        if self.full_name and self.is_playable:
            return self.full_name.lower()
        else:
            return None

    def get_embed(self) -> discord.Embed:
        title, description = abc.EmbedContentGenerator.get_embed_content("adventurer", e=self)
        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.full_name),
            colour=discord.Embed.Empty if not self.element else self.element.get_colour()
        ).set_thumbnail(
            url=util.get_wiki_cdn_url(f"{self.icon_name}.png")
        )


class Dragon(abc.Entity):
    """
    Represents a dragon and some of their associated data
    """

    repository: abc.EntityRepository = None

    @classmethod
    def get_all(cls):
        return cls.repository.data.values()

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
        mp("availability", mf.text, "Availability")
        mp("release_date", mf.date, "ReleaseDate")
        mp("rarity", mf.int, "Rarity")
        mp("element", Element.get, "ElementalTypeId")
        mp("max_hp", mf.int, "MaxHp")
        mp("max_str", mf.int, "MaxAtk")
        mp("favourite_gift", DragonGift.get, "FavoriteType")
        mp("icon_name", lambda i, v: f"{i}_0{v}", "BaseId", "VariationId")
        mp("is_playable", mf.bool, "IsPlayable")
        mp("ability_1", mf.filtered_list_of(Ability.find), *(f"Abilities1{i + 1}" for i in range(5)))
        mp("ability_2", mf.filtered_list_of(Ability.find), *(f"Abilities2{i + 1}" for i in range(5)))
        mp("skill", Skill.find, "SkillID")

        def post_processor(dragon: Dragon):
            try:
                # max might adds 300 for bond 30, 100 for skill 1
                dragon.max_might = sum((
                    dragon.max_hp,
                    dragon.max_str,
                    300,  # bond 30
                    100,  # skill 1
                    (0 if not dragon.ability_1 else dragon.ability_1[-1].might),
                    (0 if not dragon.ability_2 else dragon.ability_2[-1].might)
                ))
            except (IndexError, TypeError):
                dragon.max_might = None

            if dragon.skill:
                dragon.skill.owner.append(dragon)

            return True

        mapper.post_processor = post_processor

    def __init__(self):
        self.full_name = ""
        self.name = ""
        self.title = ""
        self.description = ""
        self.obtained = ""
        self.availability = ""
        self.release_date: Optional[datetime.datetime] = None
        self.rarity = 0
        self.element: Optional[Element] = None
        self.max_hp = 0
        self.max_str = 0
        self.max_might = 0
        self.favourite_gift: Optional[DragonGift] = None
        self.icon_name = ""
        self.skill: Optional[Skill] = None
        self.ability_1: List[Ability] = []
        self.ability_2: List[Ability] = []

        self.is_playable = True

    def __str__(self):
        return self.full_name

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key.lower())

    def get_key(self):
        if self.full_name and self.is_playable:
            return self.full_name.lower()
        else:
            return None

    def get_embed(self) -> discord.Embed:
        title, description = abc.EmbedContentGenerator.get_embed_content("dragon", e=self)
        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.full_name),
            colour=discord.Embed.Empty if not self.element else self.element.get_colour()
        ).set_thumbnail(
            url=util.get_wiki_cdn_url(f"{self.icon_name}.png")
        )


class Wyrmprint(abc.Entity):
    """
    Represents a wyrmprint and some of its associated data
    """

    repository: abc.EntityRepository = None

    @classmethod
    def get_all(cls):
        return cls.repository.data.values()

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
        mp("availability", mf.text, "Availability")
        mp("release_date", mf.date, "ReleaseDate")
        mp("icon_name", lambda i: f"{i}_02", "BaseId")
        mp("ability_1", mf.filtered_list_of(Ability.find), *(f"Abilities1{i + 1}" for i in range(3)))
        mp("ability_2", mf.filtered_list_of(Ability.find), *(f"Abilities2{i + 1}" for i in range(3)))
        mp("ability_3", mf.filtered_list_of(Ability.find), *(f"Abilities3{i + 1}" for i in range(3)))

        def post_processor(wp: Wyrmprint):
            try:
                wp.max_might = sum((
                    wp.max_hp,
                    wp.max_str,
                    (0 if not wp.ability_1 else wp.ability_1[-1].might),
                    (0 if not wp.ability_2 else wp.ability_2[-1].might),
                    (0 if not wp.ability_3 else wp.ability_3[-1].might)
                ))
            except (IndexError, TypeError):
                wp.max_might = None

            return True

        mapper.post_processor = post_processor

    def __init__(self):
        self.name = ""
        self.rarity = 0
        self.obtained = []
        self.availability = ""
        self.release_date: Optional[datetime.datetime] = None
        self.max_hp = 0
        self.max_str = 0
        self.max_might = 0
        self.icon_name = ""
        self.ability_1: List[Ability] = []
        self.ability_2: List[Ability] = []
        self.ability_3: List[Ability] = []

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
        title, description = abc.EmbedContentGenerator.get_embed_content("wyrmprint", e=self)
        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.name),
            colour=get_rarity_colour(self.rarity)
        ).set_thumbnail(
            url=util.get_wiki_cdn_url(f"{self.icon_name}.png")
        )


class Weapon(abc.Entity):
    """
    Represents a weapon and some of its associated data
    """
    repository: abc.EntityRepository = None

    @classmethod
    def get_all(cls):
        return cls.repository.data.values()

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
        mp("availability", mf.text, "Availability")
        mp("max_hp", mf.int, "MaxHp")
        mp("max_str", mf.int, "MaxAtk")
        mp("icon_name", lambda b_id, f_id: f"{b_id}_01_{f_id}", "BaseId", "FormId")
        mp("ability_1", Ability.find, "Abilities11")
        mp("ability_2", Ability.find, "Abilities21")
        mp("skill", Skill.find, "Skill")

        mapper.set_post_process_args("CraftGroupId", "CraftNodeId", "ParentCraftNodeId")

        def mapper_post_processor(weapon: Weapon):
            # max might adds 100 for skill if it exists
            try:
                weapon.max_might = sum((
                    weapon.max_hp,
                    weapon.max_str,
                    (0 if not weapon.ability_1 else weapon.ability_1.might),
                    (0 if not weapon.ability_2 else weapon.ability_2.might),
                    (0 if not weapon.skill else 100)
                ))
            except (IndexError, TypeError):
                weapon.max_might = None

            if weapon.skill:
                weapon.skill.owner.append(weapon)

            return True

        def repo_post_processor(weapons: dict):
            craft_groups = collections.defaultdict(lambda: collections.defaultdict(list))
            craft_index = {}

            w: Weapon
            for w in weapons.values():
                # add to craft groups map for second pass
                pp = getattr(w, "_POST_PROCESS")
                delattr(w, "_POST_PROCESS")
                group_id = mf.text(pp["CraftGroupId"])
                if group_id:
                    node_id = mf.text(pp["CraftNodeId"])
                    parent_node_id = mf.text(pp["ParentCraftNodeId"])
                    craft_groups[group_id][parent_node_id].append(node_id)
                    craft_index[group_id, node_id] = w

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
        self.element: Optional[Element] = None
        self.weapon_type: Optional[WeaponType] = None
        self.obtained = ""
        self.availability = ""
        self.max_hp = 0
        self.max_str = 0
        self.max_might = 0
        self.icon_name = ""
        self.skill: Optional[Skill] = None
        self.ability_1: Optional[Ability] = None
        self.ability_2: Optional[Ability] = None
        self.crafting_materials = {}
        self.crafted_from: Optional[Weapon] = None
        self.crafted_to: List[Weapon] = []
        self.tier: Optional[int] = None

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
        title, description = abc.EmbedContentGenerator.get_embed_content("weapon", e=self)

        if self.element is not None:
            colour = self.element.get_colour()
        elif self.rarity is not None:
            colour = get_rarity_colour(self.rarity)
        else:
            colour = discord.Embed.Empty

        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.name),
            colour=colour
        ).set_thumbnail(
            url=util.get_wiki_cdn_url(f"{self.icon_name}.png")
        )


class Skill(abc.Entity):
    """
    Represents a skill and some of its associated data
    """
    repository: abc.EntityRepository = None

    class SkillLevel:
        def __init__(self, desc: str, sp: int, share_sp: int):
            self.description = desc
            self.sp = sp
            self.share_sp = share_sp

        def __repr__(self):
            return str(vars(self))

    @classmethod
    def get_all(cls):
        return cls.repository.data.values()

    @classmethod
    def init(cls):
        mapper = abc.EntityMapper(Skill)
        cls.repository = abc.EntityRepository(mapper, "Skills")

        mp = mapper.add_property  # mapper property
        mf = abc.EntityMapper  # mapper functions

        def icon_name(*args):
            try:
                return list(filter(None, args))[-1]
            except IndexError:
                return None

        def map_level(desc, sp, share_sp):
            return Skill.SkillLevel(mf.text(desc), mf.int0(sp), mf.int0(share_sp))

        def skill_levels(*args):
            max_level = mf.int0(args[0])
            arg_groups = itertools.zip_longest(*([iter(args[1:])] * 3))
            mapped_levels = itertools.starmap(map_level, arg_groups)
            valid_levels = list(itertools.takewhile(lambda sl: sl.description, mapped_levels))
            return valid_levels[:max_level]

        mp("id", mf.first_of(mf.list), "SkillId")
        mp("name", mf.text, "Name")
        mp("sp_regen", mf.int0, "SpRegen")
        mp("icon_name", icon_name, "SkillLv1IconName", "SkillLv2IconName", "SkillLv3IconName", "SkillLv4IconName")
        mp("levels", skill_levels, "MaxSkillLevel",
           "Description1", "Sp",    "SpEdit",
           "Description2", "SPLv2", "SpLv2Edit",
           "Description3", "SPLv3", "SpLv3Edit",
           "Description4", "SPLv4", "SpLv4Edit")

        mapper.set_secondary_keys("SkillId", ignore_first=True)

    def __init__(self):
        self.id = ""
        self.name = ""
        self.sp_regen = 0
        self.levels: List[Skill.SkillLevel] = []
        self.owner: List[abc.Entity] = []  # updated in postprocess of Adventurer, Dragon, Weapon
        self.share_cost = 0  # assigned in postprocess of Adventurer
        self.icon_name = ""

    def __str__(self):
        return self.name

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key.lower())

    def get_key(self):
        return self.id

    def get_embed(self) -> discord.Embed:
        title, description = abc.EmbedContentGenerator.get_embed_content("skill", e=self)
        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.name),
            color=get_rarity_colour(len(self.levels) + 2)
        ).set_thumbnail(
            url=util.get_wiki_cdn_url(f"{self.icon_name}.png")
        )


class Ability(abc.Entity):
    """
    Represents an ability and some of its associated data
    """
    repository: abc.EntityRepository = None

    @classmethod
    def get_all(cls):
        return cls.repository.data.values()

    @classmethod
    def init(cls):
        def generic_name(s: str):
            text = mf.text(s)
            if not text:
                return None

            return re.sub(r"\([^)]+\)", "", text).replace("%", "").strip() or None

        mapper = abc.EntityMapper(Ability)
        cls.repository = abc.EntityRepository(mapper, "Abilities")

        mp = mapper.add_property  # mapper property
        mf = abc.EntityMapper  # mapper functions

        mp("id", mf.text, "Id")
        mp("name", mf.text, "Name")
        mp("generic_name", generic_name, "GenericName")
        mp("description", mf.text, "Details")
        mp("might", mf.int, "PartyPowerWeight")
        mp("icon_name", mf.none, "AbilityIconName")

    def __init__(self):
        self.id = ""
        self.name = ""
        self.generic_name = ""
        self.description = ""
        self.might = 0
        self.icon_name = ""

    def __str__(self):
        return self.name

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key)

    def get_key(self):
        return self.id

    def get_embed(self) -> discord.Embed:
        title, description = abc.EmbedContentGenerator.get_embed_content("ability", e=self)

        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.name),
            color=0xFF7000
        ).set_thumbnail(
            url=util.get_wiki_cdn_url(f"{self.icon_name}.png")
        )


class CoAbility(abc.Entity):
    """
    Represents a co-ability and some of its associated data
    """
    repository: abc.EntityRepository = None

    @classmethod
    def get_all(cls):
        return cls.repository.data.values()

    @classmethod
    def init(cls):
        mapper = abc.EntityMapper(CoAbility)
        cls.repository = abc.EntityRepository(mapper, "CoAbilities")

        mp = mapper.add_property  # mapper property
        mf = abc.EntityMapper  # mapper functions

        mp("id", mf.text, "Id")
        mp("name", mf.text, "Name")
        mp("generic_name", mf.text, "GenericName")
        mp("description", mf.text, "Details")
        mp("might", mf.int, "PartyPowerWeight")
        mp("icon_name", mf.none, "AbilityIconName")

    def __init__(self):
        self.id = ""
        self.name = ""
        self.generic_name = ""
        self.description = ""
        self.might = 0
        self.icon_name = ""

    def __str__(self):
        return self.name

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key)

    def get_key(self):
        return self.id

    def get_embed(self) -> discord.Embed:
        title, description = abc.EmbedContentGenerator.get_embed_content("coability", e=self)

        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.generic_name),
            color=0x006080
        ).set_thumbnail(
            url=util.get_wiki_cdn_url(f"{self.icon_name}.png")
        )


class ChainCoAbility(abc.Entity):
    """
    Represents a chain co-ability and some of its associated data
    """
    repository: abc.EntityRepository = None

    @classmethod
    def get_all(cls):
        return cls.repository.data.values()

    @classmethod
    def init(cls):
        mapper = abc.EntityMapper(ChainCoAbility)
        cls.repository = abc.EntityRepository(mapper, "ChainCoAbilities")

        mp = mapper.add_property  # mapper property
        mf = abc.EntityMapper  # mapper functions

        mp("id", mf.text, "Id")
        mp("name", mf.text, "Name")
        mp("generic_name", mf.text, "GenericName")
        mp("description", mf.text, "Details")
        mp("icon_name", mf.none, "AbilityIconName")

    def __init__(self):
        self.id = ""
        self.name = ""
        self.generic_name = ""
        self.description = ""
        self.icon_name = ""

    def __str__(self):
        return self.name

    @classmethod
    def find(cls, key: str):
        key = abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key)

    def get_key(self):
        return self.id

    def get_embed(self) -> discord.Embed:
        title, description = abc.EmbedContentGenerator.get_embed_content("chain_coability", e=self)

        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.generic_name),
            color=0x006080
        ).set_thumbnail(
            url=util.get_wiki_cdn_url(f"{self.icon_name}.png")
        )


class Showcase(abc.Entity):
    """
    Represents a summon showcase and some of its associated data
    """

    repository: abc.EntityRepository = None

    @classmethod
    def get_all(cls):
        return cls.repository.data.values()

    @classmethod
    def init(cls):
        def get_entity_list(names, key_mapper):
            if not mf.text(names):
                return []
            entity_name_list = mf.text(names).split(", ")
            return list(filter(None, map(key_mapper, entity_name_list)))

        mapper = abc.EntityMapper(Showcase)
        cls.repository = abc.EntityRepository(mapper, "SummonShowcase")

        mp = mapper.add_property  # mapper property
        mf = abc.EntityMapper  # mapper functions

        mp("name", lambda s: s.replace(" (Summon Showcase)", ""), "Title")
        mp("page_name", mf.text, "Title")
        mp("start_date", mf.date, "StartDate")
        mp("end_date", mf.date, "EndDate")
        mp("type", mf.text, "Type")
        mp("featured_adventurers", lambda s: get_entity_list(s, Adventurer.find), "Adventurer")
        mp("featured_dragons", lambda s: get_entity_list(s, Dragon.find), "Dragons")

    def __init__(self):
        self.name = ""
        self.page_name = ""
        self.type = ""
        self.start_date: Optional[datetime.datetime] = None
        self.end_date: Optional[datetime.datetime] = None
        self.featured_adventurers: List[Adventurer] = []
        self.featured_dragons: List[Dragon] = []

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
        title, description = abc.EmbedContentGenerator.get_embed_content("showcase", e=self)
        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.page_name),
            color=get_rarity_colour(5)
        )


Adventurer.init()
Dragon.init()
Wyrmprint.init()
Weapon.init()
Skill.init()
Ability.init()
CoAbility.init()
ChainCoAbility.init()
Showcase.init()
