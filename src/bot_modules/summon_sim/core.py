import discord
import textwrap
import util
import data
import random
import aiohttp
import hook
import config


default_showcase: "Showcase" = None


class Showcase(data.abc.Entity):
    """
    Represents a summon showcase and some of its associated data
    """

    repository: data.abc.EntityRepository = None

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

        mapper = data.abc.EntityMapper(Showcase)
        cls.repository = data.abc.EntityRepository(mapper, "SummonShowcase")

        mp = mapper.add_property  # mapper property
        mf = data.abc.EntityMapper  # mapper functions

        mp("name", lambda s: s.replace(" (Summon Showcase)", ""), "Title")
        mp("page_name", mf.text, "Title")
        mp("start_date", mf.date, "StartDate")
        mp("end_date", mf.date, "EndDate")
        mp("type", mf.text, "Type")
        mp("focus_adventurers", lambda s: get_entity_list(s, data.Adventurer.find), "Adventurer")
        mp("focus_dragons", lambda s: get_entity_list(s, data.Dragon.find), "Dragons")

        mapper.post_processor = Showcase.initialise

    def initialise(self):
        featured = self.focus_adventurers + self.focus_dragons
        self.is_gala = any(e.availability == "Gala" for e in featured)
        self.entity_pools = {r: {f: {t: [] for t in (data.Adventurer, data.Dragon)} for f in ("f", "n")} for r in range(3, 6)}

        for e in featured:
            if e.rarity:
                self.entity_pools[e.rarity]["f"][type(e)].append(e)

        normal_pool = (set(data.Adventurer.get_all().values()) | set(data.Dragon.get_all().values())) - set(
            featured)
        for e in normal_pool:
            if e.rarity and (e.availability == "Permanent" or (self.is_gala and e.availability == "Gala")):
                self.entity_pools[e.rarity]["n"][type(e)].append(e)

        return True

    def __init__(self):
        self.name = ""
        self.page_name = ""
        self.type = ""
        self.start_date = ""
        self.end_date = ""
        self.focus_adventurers = []
        self.focus_dragons = []
        self.is_gala = False
        self.entity_pools = {}

    @classmethod
    def find(cls, key: str):
        key = data.abc.EntityMapper.text(key)
        if key is None:
            return None
        return cls.repository.get_from_key(key.lower())

    def __str__(self):
        return self.name

    def get_key(self):
        if self.name:
            return self.name.lower()
        else:
            return None

    def get_embed(self) -> discord.Embed:
        fmt = data.abc.EmbedFormatter()

        title = fmt.format("{e.name} (Summon Showcase)", e=self)
        focus_adventurers = "\n".join(map(data.Adventurer.get_title_with_emotes, self.focus_adventurers))
        focus_dragons = "\n".join(map(data.Dragon.get_title_with_emotes, self.focus_dragons))
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
            color=data.get_rarity_colour(5)
        )

    def get_pool_rates(self, pity):
        rates = {r: {f: {t: 0 for t in (data.Adventurer, data.Dragon)} for f in ("f", "n")} for r in range(3, 6)}

        # 5* rates
        base_5_rate = 6 if self.is_gala else 4
        total_5_rate = base_5_rate + pity
        rate_multi_5 = total_5_rate / base_5_rate
        featured_5_adv_count = len(self.entity_pools[5]["f"][data.Adventurer])
        featured_5_drg_count = len(self.entity_pools[5]["f"][data.Dragon])
        rates[5]["f"][data.Adventurer] = rate_multi_5 * 0.5 * featured_5_adv_count
        rates[5]["f"][data.Dragon] = rate_multi_5 * 0.8 * featured_5_drg_count
        rates[5]["n"][data.Adventurer] = total_5_rate / 2 - rates[5]["f"][data.Adventurer]
        rates[5]["n"][data.Dragon] = total_5_rate / 2 - rates[5]["f"][data.Dragon]

        # 4* rates
        featured_4_adv_count = len(self.entity_pools[4]["f"][data.Adventurer])
        featured_4_drg_count = len(self.entity_pools[4]["f"][data.Dragon])
        featured_4_total_count = featured_4_adv_count + featured_4_drg_count
        if featured_4_total_count:
            rates[4]["f"][data.Adventurer] = 7 * featured_4_adv_count / featured_4_total_count
            rates[4]["f"][data.Dragon] = 7 * featured_4_drg_count / featured_4_total_count
            rates[4]["n"][data.Adventurer] = 5.05
            rates[4]["n"][data.Dragon] = 3.95
        else:
            rates[4]["n"][data.Adventurer] = 8.55
            rates[4]["n"][data.Dragon] = 7.45

        # 3* rates
        normal_3_rate_split = 80 - pity
        offset_3_rate = -1 if self.is_gala else 0
        featured_3_adv_count = len(self.entity_pools[3]["f"][data.Adventurer])
        featured_3_drg_count = len(self.entity_pools[3]["f"][data.Dragon])
        rates[3]["f"][data.Adventurer] = 4 * featured_3_adv_count
        rates[3]["f"][data.Dragon] = 4 * featured_3_drg_count
        rates[3]["n"][data.Adventurer] = 0.6 * normal_3_rate_split - rates[3]["f"][data.Adventurer] + offset_3_rate
        rates[3]["n"][data.Dragon] = 0.4 * normal_3_rate_split - rates[3]["f"][data.Dragon] + offset_3_rate

        return rates

    def get_five_star_rate(self, pity_progress):
        base_rate = 6 if self.is_gala else 4
        pity_rate = pity_progress // 10 * 0.5
        return base_rate + pity_rate

    def is_pity_capped(self, pity_progress):
        return pity_progress >= (60 if self.is_gala else 100)

    def _get_result(self, rates):
        weights = []
        pools = []
        for rarity, rarity_pool in self.entity_pools.items():
            for is_featured, sub_pool in rarity_pool.items():
                for e_type, type_pool in sub_pool.items():
                    pools.append(type_pool)
                    weights.append(rates[rarity][is_featured][e_type])

        selected_pool = random.choices(pools, weights=weights)[0]
        return random.choice(selected_pool)

    def perform_solo(self, pity_progress):
        pity = pity_progress // 10 * 0.5
        rates = self.get_pool_rates(pity)
        _adjust_rates(rates, guaranteed_5=self.is_pity_capped(pity_progress))
        result = self._get_result(rates)
        if result.rarity == 5:
            pity_progress = 0
        else:
            pity_progress += 1
        return result, pity_progress

    def perform_tenfold(self, pity_progress):
        pity = pity_progress // 10 * 0.5
        rates = self.get_pool_rates(pity)
        results = [self._get_result(rates) for _ in range(9)]
        received_5 = any(e.rarity == 5 for e in results)
        _adjust_rates(rates, guaranteed_5=self.is_pity_capped(pity_progress), guaranteed_4=True)
        results.append(self._get_result(rates))
        if received_5 or results[-1].rarity == 5:
            pity_progress = 0
        else:
            pity_progress += 10
        return results, pity_progress


async def update_repository():
    global default_showcase
    async with aiohttp.ClientSession() as session:
        await Showcase.repository.update_data(session)

    default_showcase = Showcase()
    default_showcase.name = "none"
    default_showcase.initialise()


def can_summon_on_showcase(showcase: Showcase):
    if showcase.name in config.get_global("general")["summonable_showcase_blacklist"]:
        return False

    return showcase.type == "Regular" and not showcase.name.startswith("Dragon Special")


def get_summonable_showcase(name: str):
    if name.lower() == "none":
        return default_showcase
    else:
        showcase = Showcase.find(name)
        if showcase and can_summon_on_showcase(showcase):
            return showcase

        return None


def get_summonable_showcase_list():
    showcases = sorted(Showcase.get_all().values(), key=lambda sc: sc.start_date, reverse=True)
    return list(filter(can_summon_on_showcase, showcases))


def get_summons_remaining(pity_progress):
    return ((-pity_progress - 1) % 10) + 1


def _adjust_rates(rates, guaranteed_5=False, guaranteed_4=False):
    if guaranteed_5:
        _set_rarity_rate(rates[3], 0)
        _set_rarity_rate(rates[4], 0)
        _set_rarity_rate(rates[5], 100)
    elif guaranteed_4:
        old_3_rate = _set_rarity_rate(rates[3], 0)
        _set_rarity_rate(rates[4], 16 + old_3_rate)


def _set_rarity_rate(rarity_rates, new_rate):
    old_rate = sum(rarity_rates["f"].values()) + sum(rarity_rates["n"].values())
    rate_scale = new_rate / old_rate
    for is_featured, type_pool in rarity_rates.items():
        for e_type in type_pool:
            type_pool[e_type] *= rate_scale

    return old_rate


Showcase.init()
hook.Hook.get("data_downloaded").attach(update_repository)
