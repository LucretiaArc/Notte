import calendar
import collections
import itertools
import discord
import re
import util
import textwrap
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
        return cls.repository.data

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
        mp("skill_1", Skill.find, "Skill1Name")
        mp("skill_2", Skill.find, "Skill2Name")
        mp("icon_name", lambda i, v, r: f"{i}_0{v}_r0{r}", "Id", "VariationId", "Rarity")

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

            for sk in [adv.skill_1, adv.skill_2]:
                if sk:
                    sk.owner.append(adv)

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
            coability_str = self.coability[-1].name or "?"
        except IndexError:
            coability_str = "?"

        try:
            chain_coability_str = self.chain_coability[-1].name or "?"
        except IndexError:
            chain_coability_str = "?"

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
                **Chain Co-ability:** {chain_coability}
                
                *Obtained from: {e.obtained}*
                *Release Date: {e.release_date!d}* 
                """),
            e=self,
            coability=coability_str,
            chain_coability=chain_coability_str
        )

        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.full_name),
            colour=discord.Embed.Empty if not self.element else self.element.get_colour()
        )

    def get_title_with_emotes(self):
        return abc.EmbedFormatter().format("{e.rarity!r}{e.element!e}{e.weapon_type!e} {e.full_name}", e=self)


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
        mp("availability", mf.text, "Availability")
        mp("release_date", mf.date, "ReleaseDate")
        mp("rarity", mf.int, "Rarity")
        mp("element", Element.get, "ElementalTypeId")
        mp("max_hp", mf.int, "MaxHp")
        mp("max_str", mf.int, "MaxAtk")
        mp("favourite_gift", DragonGift.get, "FavoriteType")
        mp("icon_name", lambda i, v: f"{i}_0{v}", "BaseId", "VariationId")

        mp("ability_1", mf.filtered_list_of(Ability.find), *(f"Abilities1{i + 1}" for i in range(2)))
        mp("ability_2", mf.filtered_list_of(Ability.find), *(f"Abilities2{i + 1}" for i in range(2)))
        mp("skill", Skill.find, "SkillName")

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

    def get_title_with_emotes(self):
        return abc.EmbedFormatter().format("{e.rarity!r}{e.element!e} {e.full_name}", e=self)


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
        mp("availability", mf.text, "Availability")
        mp("release_date", mf.date, "ReleaseDate")

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
        mp("availability", mf.text, "Availability")
        mp("max_hp", mf.int, "MaxHp")
        mp("max_str", mf.int, "MaxAtk")

        mp("ability_1", Ability.find, "Abilities11")
        mp("ability_2", Ability.find, "Abilities21")
        mp("skill", Skill.find, "SkillName")

        def crafting_materials(*args):
            arg_pairs = zip(*[iter(args)] * 2)
            return {k: util.safe_int(v, 0) for k, v in arg_pairs if k and k != "0"}

        mp("crafting_materials", crafting_materials,
           'CONCAT("Rupies")', "AssembleCoin",
           "CraftMaterial1", "CraftMaterialQuantity1",
           "CraftMaterial2", "CraftMaterialQuantity2",
           "CraftMaterial3", "CraftMaterialQuantity3",
           "CraftMaterial4", "CraftMaterialQuantity4",
           "CraftMaterial5", "CraftMaterialQuantity5",
           )

        mp(None, mf.none, "CraftGroupId", "CraftNodeId", "ParentCraftNodeId")

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
        self.element: Optional[Element] = None
        self.weapon_type: Optional[WeaponType] = None
        self.obtained = ""
        self.availability = ""

        self.max_hp = 0
        self.max_str = 0
        self.max_might = 0

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

    def get_crafting_cost(self):
        material_cost = collections.Counter()
        material_cost.update(self.crafting_materials)
        if self.crafted_from:
            prerequisite_materials = self.crafted_from.get_crafting_cost()
            material_cost.update({k: v * 5 for k, v in prerequisite_materials.items()})

        return dict(material_cost)

    def get_crafting_cost_embed(self):
        if self.obtained == "Crafting":
            crafting_cost = self.get_crafting_cost()
            content = "**Total Crafting Cost**\n" + "\n".join(f"**{k}**: {v:,}" for k, v in crafting_cost.items())

            if self.element is not None:
                colour = self.element.get_colour()
            elif self.rarity is not None:
                colour = get_rarity_colour(self.rarity)
            else:
                colour = discord.Embed.Empty

            return discord.Embed(
                title=self.get_title_string(),
                description=content,
                url=util.get_link(self.name),
                colour=colour
            )

        return None


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

        def map_level(desc, sp):
            return Skill.SkillLevel(mf.text(desc), mf.int(sp))

        def skill_levels(*args):
            max_level = mf.int0(args[0])
            arg_pairs = itertools.zip_longest(*([iter(args[1:])] * 2))
            mapped_levels = itertools.starmap(map_level, arg_pairs)
            valid_levels = list(itertools.takewhile(lambda sl: sl.description, mapped_levels))
            return valid_levels[:max_level]

        mp("name", mf.text, "Name")
        mp("levels", skill_levels, "MaxSkillLevel",
           "Description1", "Sp",
           "Description2", "SPLv2",
           "Description3", "Sp",
           "Description4", "Sp")

    def __init__(self):
        self.name = ""
        self.levels: List[Skill.SkillLevel] = []
        self.owner: List[abc.Entity] = []  # updated in postprocess

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

        if len(self.owner) == 0:
            owner_str = ""
        elif len(self.owner) == 1:
            owner_str = fmt.format("**Used by:** {owner}", owner=self.owner[0])
        else:
            owners = "\n".join(str(e) for e in self.owner[:5])
            if len(self.owner) > 5:
                owners += "\n..."
            owner_str = fmt.format("\n**Used by**\n{owner_list}", owner_list=owners)

        description = fmt.format(
            textwrap.dedent("""
                {max_level.description}

                **Cost:** {max_level.sp} SP
                {owner_str}
                """),
            e=self,
            max_level=self.levels[-1] if self.levels else Skill.SkillLevel("", 0),
            owner_str=owner_str
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

            return re.sub(r"\([^)]+\)", "", text).replace("%", "").strip() or None

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


class ChainCoAbility(abc.Entity):
    """
    Represents a chain co-ability and some of its associated data
    """
    repository: abc.EntityRepository = None

    @classmethod
    def get_all(cls):
        return cls.repository.data

    @classmethod
    def init(cls):
        mapper = abc.EntityMapper(ChainCoAbility)
        cls.repository = abc.EntityRepository(mapper, "ChainCoAbilities")

        mp = mapper.add_property  # mapper property
        mf = abc.EntityMapper  # mapper functions

        mp("id_str", mf.text, "Id")
        mp("name", mf.text, "Name")
        mp("generic_name", mf.text, "GenericName")
        mp("description", mf.text, "Details")

    def __init__(self):
        self.id_str = ""
        self.name = ""
        self.generic_name = ""
        self.description = ""

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

        title = fmt.format("{e.name} (Chain Co-Ability)", e=self)
        description = self.description or "?"

        return discord.Embed(
            title=title,
            description=description,
            url=util.get_link(self.generic_name),
            color=0x006080
        )


class Showcase(abc.Entity):
    """
    Represents a summon showcase and some of its associated data
    """

    repository: abc.EntityRepository = None

    @classmethod
    def get_all(cls):
        return cls.repository.data

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
        mp("focus_adventurers", lambda s: get_entity_list(s, Adventurer.find), "Adventurer")
        mp("focus_dragons", lambda s: get_entity_list(s, Dragon.find), "Dragons")

    def __init__(self):
        self.name = ""
        self.page_name = ""
        self.type = ""
        self.start_date = ""
        self.end_date = ""
        self.focus_adventurers = []
        self.focus_dragons = []

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

        title = fmt.format("{e.name} (Summon Showcase)", e=self)
        focus_adventurers = "\n".join(map(Adventurer.get_title_with_emotes, self.focus_adventurers))
        focus_dragons = "\n".join(map(Dragon.get_title_with_emotes, self.focus_dragons))
        focus_adventurers_section = f"**Focus Adventurers**\n{focus_adventurers}\n" if focus_adventurers else ""
        focus_dragon_section = f"**Focus Dragons**\n{focus_dragons}\n" if focus_dragons else ""

        description = fmt.format(
            textwrap.dedent("""
                {focus_adv!o}{focus_drg!o}
                **Start date:** {e.start_date!d}
                **End date:** {e.end_date!d}
                """),
            e=self,
            focus_adv=focus_adventurers_section,
            focus_drg=focus_dragon_section
        )

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
