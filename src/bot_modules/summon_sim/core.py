import data
import random
import hook
import config
import typing
import fuzzy_match
import logging

logger = logging.getLogger(__name__)


# pools are represented in a nested dict of pool[rarity: int][is_featured: bool][entity_type: type]
FeaturedRates = typing.Dict[type, float]
RarityRates = typing.Dict[bool, FeaturedRates]
Rates = typing.Dict[int, RarityRates]

FeaturedPools = typing.Dict[type, typing.List[data.abc.Entity]]
RarityPools = typing.Dict[bool, FeaturedPools]
EntityPools = typing.Dict[int, RarityPools]


class SimShowcase:
    showcase_matcher: fuzzy_match.Matcher = None
    showcases = {}
    default_showcase = None

    @classmethod
    def update_data(cls):
        default_showcase = data.Showcase()
        default_showcase.name = "none"
        cls.default_showcase = SimShowcase(default_showcase)

        new_cache = {}
        showcase_blacklist = config.get_global("general")["summonable_showcase_blacklist"]
        for sc_name, sc in data.Showcase.get_all().items():
            if sc.name not in showcase_blacklist and sc.type == "Regular" and not sc.name.startswith("Dragon Special"):
                new_cache[sc_name] = SimShowcase(sc)

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

    def __init__(self, showcase: data.Showcase):
        # noinspection PyTypeChecker
        featured_pool = showcase.featured_adventurers + showcase.featured_dragons
        self.showcase = showcase
        self.is_gala = any(e.availability == "Gala" for e in featured_pool)
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

        normal_pool = (set(data.Adventurer.get_all().values()) | set(data.Dragon.get_all().values())) - set(featured_pool)
        for e in normal_pool:
            if e.rarity and (e.availability == "Permanent" or (self.is_gala and e.availability == "Gala")):
                self.entity_pools[e.rarity][False][type(e)].append(e)

    def get_base_five_star_rate(self):
        return 6 if self.is_gala else 4

    def get_five_star_rate(self, pity_progress):
        return self.get_base_five_star_rate() + pity_progress // 10 * 0.5

    def is_pity_capped(self, pity_progress):
        return pity_progress >= (60 if self.is_gala else 100)

    def perform_solo(self, pity_progress):
        rates = self._get_pool_rates(pity_progress)
        SimShowcase._adjust_rates(rates, guaranteed_5=self.is_pity_capped(pity_progress))
        result = self._get_result(rates)
        if result.rarity == 5:
            pity_progress = 0
        else:
            pity_progress += 1
        return result, pity_progress

    def perform_tenfold(self, pity_progress):
        rates = self._get_pool_rates(pity_progress)
        results = [self._get_result(rates) for _ in range(9)]
        received_5 = any(e.rarity == 5 for e in results)
        SimShowcase._adjust_rates(rates, guaranteed_5=self.is_pity_capped(pity_progress), guaranteed_4=True)
        results.append(self._get_result(rates))
        if received_5 or results[-1].rarity == 5:
            pity_progress = 0
        else:
            pity_progress += 10
        return results, pity_progress

    def get_rate_breakdown(self, pity_progress):
        rates = self._get_pool_rates(pity_progress)
        output = ""
        for rarity, rarity_rates in rates.items():
            r_items = ""
            r_rate = 0
            for is_featured, featured_rates in rarity_rates.items():
                f_items = ""
                f_rate = 0
                for e_type, rate in featured_rates.items():
                    if rate > 0:
                        f_items += f"    {e_type.__name__}s: {rate:.{2}f}%\n"
                        f_rate += rate
                if f_rate > 0:
                    r_items += f"  {'Featured' if is_featured else 'Normal'}: {f_rate:.{2}f}%\n{f_items}"
                    r_rate += f_rate
            if r_rate > 0:
                output += f"**{rarity}★: {r_rate:.{2}f}%**\n{r_items}\n"
        return output.strip()

    @staticmethod
    def _get_sub_pool_rate_breakdown(pool: dict):
        combined_rate = 0
        for k, v in pool.items():
            if isinstance(v, dict):
                combined_rate += SimShowcase._get_sub_pool_rate_breakdown(v)
            else:
                combined_rate += v

    def _get_pool_rates(self, pity_progress):
        rates: Rates = {
            r: {
                f: {
                    t: 0 for t in (data.Adventurer, data.Dragon)
                } for f in (True, False)
            } for r in (5, 4, 3)
        }

        pity = pity_progress // 10 * 0.5

        # 5* rates
        base_5_rate = self.get_base_five_star_rate()
        total_5_rate = base_5_rate + pity
        rate_multi_5 = total_5_rate / base_5_rate
        featured_5_adv_count = len(self.entity_pools[5][True][data.Adventurer])
        featured_5_drg_count = len(self.entity_pools[5][True][data.Dragon])
        rates[5][True][data.Adventurer] = rate_multi_5 * 0.5 * featured_5_adv_count
        rates[5][True][data.Dragon] = rate_multi_5 * 0.8 * featured_5_drg_count
        rates[5][False][data.Adventurer] = total_5_rate / 2 - rates[5][True][data.Adventurer]
        rates[5][False][data.Dragon] = total_5_rate / 2 - rates[5][True][data.Dragon]

        # 4* rates
        featured_4_adv_count = len(self.entity_pools[4][True][data.Adventurer])
        featured_4_drg_count = len(self.entity_pools[4][True][data.Dragon])
        featured_4_total_count = featured_4_adv_count + featured_4_drg_count
        if featured_4_total_count:
            rates[4][True][data.Adventurer] = 7 * featured_4_adv_count / featured_4_total_count
            rates[4][True][data.Dragon] = 7 * featured_4_drg_count / featured_4_total_count
            rates[4][False][data.Adventurer] = 5.05
            rates[4][False][data.Dragon] = 3.95
        else:
            rates[4][False][data.Adventurer] = 8.55
            rates[4][False][data.Dragon] = 7.45

        # 3* rates
        normal_3_rate_split = 80 - pity
        offset_3_rate = (4 - self.get_base_five_star_rate()) / 2
        featured_3_adv_count = len(self.entity_pools[3][True][data.Adventurer])
        featured_3_drg_count = len(self.entity_pools[3][True][data.Dragon])
        rates[3][True][data.Adventurer] = 4 * featured_3_adv_count
        rates[3][True][data.Dragon] = 4 * featured_3_drg_count
        rates[3][False][data.Adventurer] = 0.6 * normal_3_rate_split - rates[3][False][data.Adventurer] + offset_3_rate
        rates[3][False][data.Dragon] = 0.4 * normal_3_rate_split - rates[3][False][data.Dragon] + offset_3_rate

        return rates

    def _get_result(self, rates: Rates):
        weights = []
        pools = []
        for rarity, rarity_pool in self.entity_pools.items():
            for is_featured, sub_pool in rarity_pool.items():
                for e_type, type_pool in sub_pool.items():
                    pools.append(type_pool)
                    weights.append(rates[rarity][is_featured][e_type])

        selected_pool = random.choices(pools, weights=weights)[0]
        return random.choice(selected_pool)

    @staticmethod
    def _adjust_rates(rates: Rates, guaranteed_5=False, guaranteed_4=False):
        if guaranteed_5:
            SimShowcase._set_rarity_rate(rates[3], 0)
            SimShowcase._set_rarity_rate(rates[4], 0)
            SimShowcase._set_rarity_rate(rates[5], 100)
        elif guaranteed_4:
            old_3_rate = SimShowcase._set_rarity_rate(rates[3], 0)
            SimShowcase._set_rarity_rate(rates[4], 16 + old_3_rate)

    @staticmethod
    def _set_rarity_rate(rarity_rate_pool: RarityRates, new_rate):
        old_rate = sum(rarity_rate_pool[True].values()) + sum(rarity_rate_pool[False].values())
        rate_scale = new_rate / old_rate
        for is_featured, type_pool in rarity_rate_pool.items():
            for e_type in type_pool:
                type_pool[e_type] *= rate_scale

        return old_rate


hook.Hook.get("data_downloaded").attach(SimShowcase.update_data)
