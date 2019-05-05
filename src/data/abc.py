import abc
import discord


class Entity(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def init(cls):
        pass

    @abc.abstractmethod
    def get_simple_name(self) -> str:
        return ""

    @abc.abstractmethod
    def get_key(self) -> str:
        return ""

    @abc.abstractmethod
    def get_embed(self) -> discord.Embed:
        return discord.Embed()

    def __str__(self):
        return str(vars(self))
