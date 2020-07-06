import data
import typing
import abc
from . import core, pool


class GalaBase(core.SimShowcase, abc.ABC):
    PITY_PROGRESS_MAX = 60
    FIVE_STAR_ADV_RATE_TOTAL = 3.0
    FIVE_STAR_DRG_RATE_TOTAL = 3.0

    @staticmethod
    def is_entity_in_normal_pool(e: typing.Union[data.Adventurer, data.Dragon]):
        return e.availability in ("Permanent", "Gala")

    def get_three_star_rates(self, pity_progress) -> pool.RarityRates:
        rates = core.SimShowcase.get_three_star_rates(self, pity_progress)
        rates[False][data.Adventurer] -= 1
        rates[False][data.Dragon] -= 1
        return rates


class GalaGeneric(GalaBase):
    @staticmethod
    def is_matching_showcase_type(showcase: data.Showcase):
        # noinspection PyTypeChecker
        return any(e.availability == "Gala" for e in (showcase.featured_adventurers + showcase.featured_dragons))


class GalaMultiFeatured(GalaBase):
    FIVE_STAR_ADV_RATE_EACH = 0.2
    FIVE_STAR_DRG_RATE_EACH = 0.2  # speculation, no such showcase has existed with dragons featured

    @staticmethod
    def is_matching_showcase_type(showcase: data.Showcase):
        # noinspection PyTypeChecker
        featured_pool = showcase.featured_adventurers + showcase.featured_dragons
        return len(featured_pool) > 1 and all(e.availability == "Gala" for e in featured_pool)


class ElementFocus(core.SimShowcase, abc.ABC):
    FIVE_STAR_ADV_RATE_EACH = 0.0
    FIVE_STAR_DRG_RATE_EACH = 0.0

    def get_four_star_rates(self, pity_progress) -> pool.RarityRates:
        rates = pool.RarityRates()
        rates[False][data.Adventurer] = 13.0
        rates[False][data.Dragon] = 3.0
        return rates

    def get_three_star_rates(self, pity_progress) -> pool.RarityRates:
        rates = pool.RarityRates()

        total_rate = 80 - self.get_pity_percent(pity_progress)
        rates[False][data.Adventurer] = 0.625 * total_rate
        rates[False][data.Dragon] = 0.375 * total_rate

        return rates


class LightFocus(ElementFocus):
    @staticmethod
    def is_entity_in_normal_pool(e: typing.Union[data.Adventurer, data.Dragon]):
        return e.availability == "Permanent" and e.element == data.Element.LIGHT

    @staticmethod
    def is_matching_showcase_type(showcase: data.Showcase):
        return showcase.name.startswith("Light Focus")


class WaterFocus(ElementFocus):
    @staticmethod
    def is_entity_in_normal_pool(e: typing.Union[data.Adventurer, data.Dragon]):
        return e.availability == "Permanent" and e.element == data.Element.WATER

    @staticmethod
    def is_matching_showcase_type(showcase: data.Showcase):
        return showcase.name.startswith("Water Focus")


# Overrides

class DashOfDisasterPartTwo(core.NormalSS):
    @staticmethod
    def is_matching_showcase_type(showcase: data.Showcase):
        return showcase.name == "A Dash of Disaster (Part Two)"

    def get_four_star_rates(self, pity_progress) -> pool.RarityRates:
        rates = pool.RarityRates()
        rates[False][data.Adventurer] = 8.0
        rates[False][data.Dragon] = 8.0
        return rates


class KindredTiesPartTwo(core.NormalSS):
    FIVE_STAR_ADV_RATE_EACH = 0.8

    @staticmethod
    def is_matching_showcase_type(showcase: data.Showcase):
        return showcase.name == "Fire Emblem: Kindred Ties (Part Two)"


class GalaApr2020(GalaBase):
    FIVE_STAR_ADV_RATE_TOTAL = 2.4
    FIVE_STAR_DRG_RATE_TOTAL = 3.6

    @staticmethod
    def is_matching_showcase_type(showcase: data.Showcase):
        return showcase.name == "Gala Dragalia (Apr 2020)"


class GalaMay2020(GalaBase):
    FIVE_STAR_ADV_RATE_TOTAL = 3.2
    FIVE_STAR_DRG_RATE_TOTAL = 2.8

    @staticmethod
    def is_matching_showcase_type(showcase: data.Showcase):
        return showcase.name == "Gala Dragalia (May 2020)"
