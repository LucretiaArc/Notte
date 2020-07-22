import data
import hook
import config
import fuzzy_match
import logging
import random
import typing
import abc
from . import pool


logger = logging.getLogger(__name__)


# pools are represented in a nested dict of pool[rarity: int][is_featured: bool][entity_type: type]
FeaturedPools = typing.Dict[type, typing.List[data.abc.Entity]]
RarityPools = typing.Dict[bool, FeaturedPools]
EntityPools = typing.Dict[int, RarityPools]


class SimShowcaseCache:
    showcase_matcher: fuzzy_match.Matcher = None
    showcases = {}
    default_showcase = None

    @classmethod
    def update_data(cls):
        default_showcase = data.Showcase()
        default_showcase.name = "none"
        cls.default_showcase = NormalSS(default_showcase)

        new_cache = {}
        showcase_blacklist = config.get_global("general")["summonable_showcase_blacklist"]
        for sc in data.Showcase.get_all():
            if sc.name not in showcase_blacklist:
                if sc.type == "Regular" and not sc.name.startswith("Dragon Special"):
                    new_cache[sc.get_key()] = SimShowcaseFactory.create_showcase(sc)

        matcher_additions = new_cache.copy()
        aliases = config.get_global(f"query_alias/showcase")
        for alias, expanded in aliases.items():
            try:
                matcher_additions[alias] = new_cache[expanded]
            except KeyError:
                continue

        # add fuzzy matching names
        name_replacements = {
            "part one": "part 1",
            "part two": "part 2",
        }
        matcher = fuzzy_match.Matcher(lambda s: 1 + 0.5 * len(s))
        for sc_name, sim_sc in matcher_additions.items():
            matcher.add(sc_name, sim_sc)
            for old, new in name_replacements.items():
                if old in sc_name:
                    matcher.add(sc_name.replace(old, new), sim_sc)

        cls.showcases = new_cache
        cls.showcase_matcher = matcher

    @classmethod
    def get(cls, name: str):
        if name.lower() == "none":
            return cls.default_showcase
        else:
            return cls.showcases.get(name.lower())

    @classmethod
    def match(cls, name: str):
        if name.lower() == "none":
            return cls.default_showcase
        else:
            result = cls.showcase_matcher.match(name)
            return result[0] if result else None


class SimShowcaseFactory:
    showcase_types = []

    @classmethod
    def register(cls, registered_class):
        cls.showcase_types.append(registered_class)

    @classmethod
    def create_showcase(cls, showcase: data.Showcase):
        matching_types = list(filter(lambda c: c.is_matching_showcase_type(showcase), cls.showcase_types))

        if len(matching_types) == 0:
            showcase_type = NormalSS
        elif len(matching_types) == 1:
            showcase_type = matching_types[0]
        else:
            showcase_type = matching_types[-1]

        return showcase_type(showcase)


class SimShowcase(abc.ABC):
    PITY_PROGRESS_MAX = 100
    FIVE_STAR_ADV_RATE_TOTAL = 2.0
    FIVE_STAR_DRG_RATE_TOTAL = 2.0
    FIVE_STAR_RATE_TOTAL = 4.0
    FIVE_STAR_ADV_RATE_EACH = 0.5
    FIVE_STAR_DRG_RATE_EACH = 0.8

    def __init__(self, showcase: data.Showcase):
        # noinspection PyTypeChecker
        featured_pool = showcase.featured_adventurers + showcase.featured_dragons
        self.showcase = showcase
        self.entity_pools: EntityPools = {
            r: {
                f: {
                    t: [] for t in (data.Adventurer, data.Dragon)
                } for f in (True, False)
            } for r in (5, 4, 3)
        }

        for e in featured_pool:
            if e.rarity:
                self.entity_pools[e.rarity][True][type(e)].append(e)

        normal_pool = (set(data.Adventurer.get_all()) | set(data.Dragon.get_all())) - set(featured_pool)
        for e in normal_pool:
            if e.rarity and self.is_entity_in_normal_pool(e):
                self.entity_pools[e.rarity][False][type(e)].append(e)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.FIVE_STAR_RATE_TOTAL = cls.FIVE_STAR_ADV_RATE_TOTAL + cls.FIVE_STAR_DRG_RATE_TOTAL
        SimShowcaseFactory.register(cls)

    def perform_solo(self, pity_progress):
        rates = self.get_rates(pity_progress)
        if pity_progress >= self.PITY_PROGRESS_MAX:
            rates.guarantee_five_star()
        result = self.get_result(rates)
        if result.rarity == 5:
            pity_progress = 0
        else:
            pity_progress += 1
        return result, pity_progress

    def perform_tenfold(self, pity_progress):
        rates = self.get_rates(pity_progress)
        results = [self.get_result(rates) for _ in range(9)]
        if pity_progress >= self.PITY_PROGRESS_MAX:
            rates.guarantee_five_star()
        else:
            rates.guarantee_four_star()
        results.append(self.get_result(rates))

        if any(e.rarity == 5 for e in results):
            pity_progress = 0
        else:
            pity_progress += 10
        return results, pity_progress

    def get_result(self, rates: pool.Rates):
        weights = []
        pools = []
        for rarity, rarity_pool in self.entity_pools.items():
            for is_featured, sub_pool in rarity_pool.items():
                for e_type, type_pool in sub_pool.items():
                    pools.append(type_pool)
                    weights.append(rates[rarity][is_featured][e_type])

        selected_pool = random.choices(pools, weights=weights)[0]
        return random.choice(selected_pool)

    def get_rates(self, pity_progress):
        rates = pool.Rates()
        rates[5] = self.get_five_star_rates(pity_progress)
        rates[4] = self.get_four_star_rates(pity_progress)
        rates[3] = self.get_three_star_rates(pity_progress)
        return rates

    def get_five_star_rates(self, pity_progress) -> pool.RarityRates:
        rates = pool.RarityRates()

        rate_multi = (self.FIVE_STAR_RATE_TOTAL + self.get_pity_percent(pity_progress)) / self.FIVE_STAR_RATE_TOTAL
        featured_adv_count = len(self.entity_pools[5][True][data.Adventurer])
        featured_drg_count = len(self.entity_pools[5][True][data.Dragon])
        rates[True][data.Adventurer] = rate_multi * self.FIVE_STAR_ADV_RATE_EACH * featured_adv_count
        rates[True][data.Dragon] = rate_multi * self.FIVE_STAR_DRG_RATE_EACH * featured_drg_count
        rates[False][data.Adventurer] = rate_multi * self.FIVE_STAR_ADV_RATE_TOTAL - rates[True][data.Adventurer]
        rates[False][data.Dragon] = rate_multi * self.FIVE_STAR_DRG_RATE_TOTAL - rates[True][data.Dragon]

        return rates

    def get_four_star_rates(self, pity_progress) -> pool.RarityRates:
        rates = pool.RarityRates()

        featured_adv_count = len(self.entity_pools[4][True][data.Adventurer])
        featured_drg_count = len(self.entity_pools[4][True][data.Dragon])
        featured_count = featured_adv_count + featured_drg_count
        if featured_count:
            rates[True][data.Adventurer] = 7 * featured_adv_count / featured_count
            rates[True][data.Dragon] = 7 * featured_drg_count / featured_count
            rates[False][data.Adventurer] = 5.05
            rates[False][data.Dragon] = 3.95
        else:
            rates[False][data.Adventurer] = 8.55
            rates[False][data.Dragon] = 7.45

        return rates

    def get_three_star_rates(self, pity_progress) -> pool.RarityRates:
        rates = pool.RarityRates()

        total_rate = 80 - self.get_pity_percent(pity_progress)
        featured_adv_count = len(self.entity_pools[3][True][data.Adventurer])
        featured_drg_count = len(self.entity_pools[3][True][data.Dragon])
        rates[True][data.Adventurer] = 4 * featured_adv_count
        rates[True][data.Dragon] = 4 * featured_drg_count
        rates[False][data.Adventurer] = 0.6 * total_rate - rates[True][data.Adventurer]
        rates[False][data.Dragon] = 0.4 * total_rate - rates[True][data.Dragon]

        return rates

    @staticmethod
    @abc.abstractmethod
    def is_entity_in_normal_pool(e: typing.Union[data.Adventurer, data.Dragon]):
        pass

    @staticmethod
    @abc.abstractmethod
    def is_matching_showcase_type(showcase: data.Showcase):
        pass

    @staticmethod
    def get_pity_percent(pity_progress):
        return pity_progress // 10 * 0.5


class NormalSS(SimShowcase):
    @staticmethod
    def is_entity_in_normal_pool(e: typing.Union[data.Adventurer, data.Dragon]):
        return e.availability == "Permanent"

    @staticmethod
    def is_matching_showcase_type(showcase: data.Showcase):
        return True


hook.Hook.get("data_downloaded").attach(SimShowcaseCache.update_data)
