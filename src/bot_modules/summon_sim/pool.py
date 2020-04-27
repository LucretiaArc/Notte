import collections.abc
import abc
import data
import textwrap


class RatePool(collections.abc.MutableMapping):
    def __init__(self):
        self.data = dict()

    @abc.abstractmethod
    def __getitem__(self, key):
        pass

    @abc.abstractmethod
    def __setitem__(self, key, value):
        pass

    @abc.abstractmethod
    def __delitem__(self, key):
        pass

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def get_total(self) -> float:
        combined_rate = 0.0
        for v in self.data.values():
            if isinstance(v, RatePool):
                combined_rate += v.get_total()
            else:
                combined_rate += v
        return combined_rate

    def set_total(self, new_total) -> float:
        old_total = self.get_total()
        self.scale_total(new_total / old_total)
        return old_total

    def scale_total(self, factor):
        for k, v in self.data.items():
            if isinstance(v, RatePool):
                v.scale_total(factor)
            else:
                self[k] = factor * v

    @abc.abstractmethod
    def get_breakdown(self) -> str:
        pass


class Rates(RatePool):
    def __init__(self):
        super().__init__()
        for rarity in (5, 4, 3):
            self.data[rarity] = RarityRates()

    def __getitem__(self, key: int):
        if key not in (3, 4, 5):
            raise KeyError(f"Invalid rarity {key}")
        return self.data[key]

    def __setitem__(self, key, value):
        if key not in (3, 4, 5):
            raise KeyError(f"Invalid rarity {key}")
        if isinstance(value, RarityRates):
            self.data[key] = value
        else:
            raise ValueError(f"Cannot assign {type(value)} to rarity rate pool")

    def __delitem__(self, key):
        del self.data[key]

    def get_breakdown(self) -> str:
        text_output = ""
        for rarity, rarity_rates in self.data.items():
            rarity_breakdown = textwrap.indent(rarity_rates.get_breakdown(), "\t")
            rate_total = rarity_rates.get_total()
            if rate_total > 0:
                text_output += f"**{rarity}★: {rate_total:.{2}f}%**\n{rarity_breakdown}\n"
        return text_output.strip()

    def guarantee_four_star(self):
        old_3_rate = self[3].set_total(0)
        self[4].set_total(16 + old_3_rate)

    def guarantee_five_star(self):
        self[3].set_total(0)
        self[4].set_total(0)
        self[5].set_total(100)


class RarityRates(RatePool):
    def __init__(self):
        super().__init__()
        for is_featured in (True, False):
            self.data[is_featured] = FeaturedStatusRates()

    def __getitem__(self, key: int):
        if key not in (True, False):
            raise KeyError(f"Invalid featured status")
        return self.data[key]

    def __setitem__(self, key, value):
        if key not in (True, False):
            raise KeyError(f"Invalid featured status")

        if isinstance(value, RarityRates):
            self.data[key] = value
        else:
            raise ValueError(f"Cannot assign {type(value)} to featured status rate pool")

    def __delitem__(self, key):
        del self.data[key]

    def get_breakdown(self) -> str:
        text_output = ""
        for is_featured, featured_rates in self.data.items():
            featured_breakdown = textwrap.indent(featured_rates.get_breakdown(), "\t")
            rate_total = featured_rates.get_total()
            if rate_total > 0:
                text_output += f"{'Featured' if is_featured else 'Normal'}: {rate_total:.{2}f}%\n{featured_breakdown}"
        return text_output


class FeaturedStatusRates(RatePool):
    def __init__(self):
        super().__init__()
        for entity_type in (data.Adventurer, data.Dragon):
            self.data[entity_type] = 0.0

    def __getitem__(self, key: int):
        if key not in (data.Adventurer, data.Dragon):
            raise KeyError(f"Invalid entity type {key}")
        return self.data[key]

    def __setitem__(self, key, value):
        if key not in (data.Adventurer, data.Dragon):
            raise KeyError(f"Invalid entity type {key}")
        if isinstance(value, (int, float)) and value >= 0:
            self.data[key] = value
        else:
            raise ValueError(f"Invalid rate value {value}")

    def __delitem__(self, key):
        del self.data[key]

    def get_breakdown(self) -> str:
        text_output = ""
        for e_type, rate in self.data.items():
            if rate > 0:
                text_output += f"{e_type.__name__}s: {rate:.{2}f}%\n"
        return text_output
