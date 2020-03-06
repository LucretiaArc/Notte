import json
import discord
import copy
import logging
import typing
import util
import aiofiles
import pathlib
import os

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, content: dict = None):
        if content:
            for k, v in content.items():
                setattr(self, k, v)
        self._frozen = True

    def __setattr__(self, key, value):
        if type(value) not in (dict, list, tuple, str, int, float, bool, type(None)):
            raise ValueError(f"{type(value)} cannot be encoded as JSON (see https://docs.python.org/3/library/json.html#json.JSONEncoder)")

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
        self.news_ids = []
        self.news_update_time = 0

        super().__init__(content)


static_config_cache = {}
guild_config_cache: typing.Dict[str, GuildConfig] = {}
writeable_config_cache: typing.Optional[WriteableConfig] = None


def get_global(path: str) -> dict:
    if path not in static_config_cache:
        with open(util.path(f"config/{path}.json"), encoding="utf_8") as file:
            static_config_cache[path] = json.load(file)

    return static_config_cache[path]


def get_writeable() -> WriteableConfig:
    if not writeable_config_cache:
        _load_writeable()
    return WriteableConfig(copy.deepcopy(writeable_config_cache.get_dict()))


def get_guild(guild: discord.Guild) -> GuildConfig:
    if str(guild.id) not in guild_config_cache:
        _load_guild(guild.id)
    return GuildConfig(copy.deepcopy(guild_config_cache[str(guild.id)].get_dict()))


async def set_writeable(new_config: WriteableConfig):
    global writeable_config_cache
    writeable_config_cache = WriteableConfig(copy.deepcopy(new_config.get_dict()))
    async with aiofiles.open(util.path("data/config/global.json"), "w") as file:
        await file.write(json.dumps(writeable_config_cache.get_dict()))
    logger.info("Saved writeable config")


async def set_guild(guild: discord.Guild, new_config: GuildConfig):
    global guild_config_cache
    guild_config_cache[str(guild.id)] = GuildConfig(copy.deepcopy(new_config.get_dict()))
    async with aiofiles.open(util.path(f"data/config/guild/{guild.id}.json"), "w") as file:
        await file.write(json.dumps(guild_config_cache[str(guild.id)].get_dict()))
    logger.info(f"Saved config for guild {guild.id}")


def get_prefix(guild: discord.Guild):
    return get_guild(guild).token if guild else "!!"


def _load_writeable():
    global writeable_config_cache
    path = util.path("data/config/global.json")
    should_write = False
    try:
        with open(path) as file:
            config_json = json.load(file)
            config_obj = WriteableConfig(config_json)
            writeable_config_cache = config_obj
            if not config_obj.get_dict().keys() <= config_json.keys():
                should_write = True
    except FileNotFoundError:
        writeable_config_cache = WriteableConfig()
        should_write = True

    if should_write:
        with open(path, "w") as file:
            json.dump(writeable_config_cache.get_dict(), file)


def _load_guild(guild_id: str):
    global guild_config_cache
    path = util.path(f"data/config/guild/{guild_id}.json")
    should_write = False
    try:
        with open(path) as file:
            config_json = json.load(file)
            config_obj = GuildConfig(config_json)
            guild_config_cache[str(guild_id)] = config_obj
            if not config_obj.get_dict().keys() <= config_json.keys():
                should_write = True
    except FileNotFoundError:
        guild_config_cache[str(guild_id)] = GuildConfig()
        should_write = True

    if should_write:
        with open(path, "w") as file:
            json.dump(guild_config_cache[str(guild_id)].get_dict(), file)


def init_configuration():
    os.makedirs(util.path("data/config/guild"), exist_ok=True)

    _load_writeable()
    for path in pathlib.Path(util.path("data/config/guild")).iterdir():
        if path.suffix == ".json":
            _load_guild(path.stem)
