import json
import discord
import copy
import logging
import aiofiles
import asyncio
import typing
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, content: dict = None):
        if content:
            for k, v in content.items():
                setattr(self, k, v)
        self._frozen = True

    def __setattr__(self, key, value):
        if hasattr(self, key) or not hasattr(self, "_frozen"):
            object.__setattr__(self, key, value)
        else:
            raise ValueError(f"No such configuration key '{key}'")

    def get_dict(self):
        attrs_dict = copy.deepcopy(self.__dict__)
        del attrs_dict["_frozen"]
        return attrs_dict


class GuildConfig(Config):
    def __init__(self, content=None):
        self.token = "!!"
        self.active_channel = 0

        super().__init__(content)


class WriteableConfig(Config):
    def __init__(self, content=None):
        self.news_recent_article_ids = []
        self.news_recent_article_date = 0
        self.void_order = []
        self.void_availability = {}

        super().__init__(content)


data_path = Path("../data")
os.makedirs(data_path / "guild", exist_ok=True)

static_config_cache = {}
guild_config_cache: typing.Dict[int, GuildConfig] = {}
writeable_config_cache: WriteableConfig = None


def get_global(path: str):
    if path not in static_config_cache:
        with open(Path(f"config/{path}.json")) as file:
            static_config_cache[path] = json.load(file)

    return static_config_cache[path]


def get_guild(guild: discord.Guild) -> GuildConfig:
    global guild_config_cache
    guild_id = guild.id
    if guild_id not in guild_config_cache:
        file_path = data_path / f"guild/{guild_id}.json"
        try:
            with open(file_path) as file:
                guild_config_cache[guild_id] = GuildConfig(json.load(file))
        except FileNotFoundError:
            guild_config_cache[guild_id] = GuildConfig()
            asyncio.ensure_future(set_guild(guild, GuildConfig()))
    return GuildConfig(copy.deepcopy(guild_config_cache[guild_id].get_dict()))


async def set_guild(guild: discord.Guild, new_config: GuildConfig):
    global guild_config_cache
    guild_id = guild.id
    file_path = data_path / f"guild/{guild_id}.json"
    guild_config_cache[guild_id] = GuildConfig(copy.deepcopy(new_config.get_dict()))
    async with aiofiles.open(file_path, "w") as file:
        await file.write(json.dumps(guild_config_cache[guild_id].get_dict()))


def get_writeable() -> WriteableConfig:
    global writeable_config_cache
    if not writeable_config_cache:
        file_path = data_path / "writeable_config.json"
        try:
            with open(file_path) as file:
                writeable_config_cache = WriteableConfig(json.load(file))
        except FileNotFoundError:
            writeable_config_cache = WriteableConfig()
            asyncio.ensure_future(set_writeable(WriteableConfig()))
    return WriteableConfig(copy.deepcopy(writeable_config_cache.get_dict()))


async def set_writeable(new_config: WriteableConfig):
    global writeable_config_cache
    file_path = data_path / "writeable_config.json"
    writeable_config_cache = WriteableConfig(copy.deepcopy(new_config.get_dict()))
    async with aiofiles.open(file_path, "w") as file:
        await file.write(json.dumps(writeable_config_cache.get_dict()))


def get_prefix(guild: discord.Guild):
    return get_guild(guild).token if guild else "!!"
