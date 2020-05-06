import data
import typing
from . import core, pool


def get_gala_three_star_rates(self, pity_progress) -> pool.RarityRates:
    rates = core.SimShowcase.get_three_star_rates(self, pity_progress)
    rates[False][data.Adventurer] -= 1
    rates[False][data.Dragon] -= 1
    return rates


class GalaMultiFeatured(core.SimShowcase):
    PITY_PROGRESS_MAX = 60
    FIVE_STAR_ADV_RATE_TOTAL = 3.0
    FIVE_STAR_DRG_RATE_TOTAL = 3.0
    FIVE_STAR_ADV_RATE_EACH = 0.2
    FIVE_STAR_DRG_RATE_EACH = 0.2  # speculation, no such showcase has existed with dragons featured

    @staticmethod
    def is_entity_in_normal_pool(e: typing.Union[data.Adventurer, data.Dragon]):
        return e.availability in ("Permanent", "Gala")

    @staticmethod
    def is_matching_showcase_type(showcase: data.Showcase):
        # noinspection PyTypeChecker
        featured_pool = showcase.featured_adventurers + showcase.featured_dragons
        return len(featured_pool) > 1 and all(e.availability == "Gala" for e in featured_pool)

    def get_three_star_rates(self, pity_progress) -> pool.RarityRates:
        return get_gala_three_star_rates(self, pity_progress)


class GalaAdventurer(core.SimShowcase):
    PITY_PROGRESS_MAX = 60
    FIVE_STAR_ADV_RATE_TOTAL = 3.0
    FIVE_STAR_DRG_RATE_TOTAL = 3.0

    @staticmethod
    def is_entity_in_normal_pool(e: typing.Union[data.Adventurer, data.Dragon]):
        return e.availability in ("Permanent", "Gala")

    @staticmethod
    def is_matching_showcase_type(showcase: data.Showcase):
        return (len(showcase.featured_adventurers) == 1
                and showcase.featured_adventurers[0].availability == "Gala"
                and not showcase.featured_dragons)

    def get_three_star_rates(self, pity_progress) -> pool.RarityRates:
        return get_gala_three_star_rates(self, pity_progress)


class GalaDragon(core.SimShowcase):
    PITY_PROGRESS_MAX = 60
    FIVE_STAR_ADV_RATE_TOTAL = 2.4
    FIVE_STAR_DRG_RATE_TOTAL = 3.6

    @staticmethod
    def is_entity_in_normal_pool(e: typing.Union[data.Adventurer, data.Dragon]):
        return e.availability in ("Permanent", "Gala")

    @staticmethod
    def is_matching_showcase_type(showcase: data.Showcase):
        return (len(showcase.featured_dragons) == 1
                and showcase.featured_dragons[0].availability == "Gala"
                and not showcase.featured_adventurers)

    def get_three_star_rates(self, pity_progress) -> pool.RarityRates:
        return get_gala_three_star_rates(self, pity_progress)


# Overrides

class DashOfDisasterPartTwo(core.SimShowcase):
    @staticmethod
    def is_entity_in_normal_pool(e: typing.Union[data.Adventurer, data.Dragon]):
        return e.availability == "Permanent"

    @staticmethod
    def is_matching_showcase_type(showcase: data.Showcase):
        return showcase.name == "A Dash of Disaster (Part Two)"

    def get_four_star_rates(self, pity_progress) -> pool.RarityRates:
        rates = pool.RarityRates()
        rates[False][data.Adventurer] = 8.0
        rates[False][data.Dragon] = 8.0
        return rates


class KindredTiesPartTwo(core.SimShowcase):
    FIVE_STAR_ADV_RATE_EACH = 0.8

    @staticmethod
    def is_entity_in_normal_pool(e: typing.Union[data.Adventurer, data.Dragon]):
        return e.availability == "Permanent"

    @staticmethod
    def is_matching_showcase_type(showcase: data.Showcase):
        return showcase.name == "Fire Emblem: Kindred Ties (Part Two)"
