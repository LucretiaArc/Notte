import json
import discord
import copy
import logging
import typing
import os
import boto3
import botocore
import time
import io
import threading
from pathlib import Path

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
writeable_config_cache: WriteableConfig = None

s3_guild_object = boto3.resource('s3').Object(os.environ["S3_BUCKET_NAME"], os.environ["GUILD_CONFIG_KEY"])
s3_writeable_object = boto3.resource('s3').Object(os.environ["S3_BUCKET_NAME"], os.environ["WRITEABLE_CONFIG_KEY"])

_guild_config_modified = threading.Event()
_writeable_config_modified = threading.Event()
_writeable_sync_thread = None
_guild_sync_thread = None


def get_global(path: str) -> dict:
    if path not in static_config_cache:
        with open(Path(f"../config/{path}.json"), encoding="utf_8") as file:
            static_config_cache[path] = json.load(file)

    return static_config_cache[path]


def get_guild(guild: discord.Guild) -> GuildConfig:
    if str(guild.id) not in guild_config_cache:
        set_guild(guild, GuildConfig())
        return GuildConfig()

    return GuildConfig(copy.deepcopy(guild_config_cache[str(guild.id)].get_dict()))


def set_guild(guild: discord.Guild, new_config: GuildConfig):
    guild_config_cache[str(guild.id)] = GuildConfig(copy.deepcopy(new_config.get_dict()))
    _guild_config_modified.set()


def get_writeable() -> WriteableConfig:
    return WriteableConfig(copy.deepcopy(writeable_config_cache.get_dict()))


def set_writeable(new_config: WriteableConfig):
    global writeable_config_cache
    writeable_config_cache = WriteableConfig(copy.deepcopy(new_config.get_dict()))
    _writeable_config_modified.set()


def get_prefix(guild: discord.Guild):
    return get_guild(guild).token if guild else "!!"


def init_configuration():
    global guild_config_cache, writeable_config_cache, _guild_sync_thread, _writeable_sync_thread

    # fetch configs from S3
    writeable_config = _fetch_config(s3_writeable_object, "writeable config")
    writeable_config_cache = WriteableConfig(writeable_config)
    guild_configs = _fetch_config(s3_guild_object, "guild configs")
    guild_config_cache = {guild_id: GuildConfig(config) for guild_id, config in guild_configs.items()}

    # ensure missing keys are written back with defaults
    wc_keys = WriteableConfig().get_dict().keys()
    if not wc_keys <= writeable_config.keys():
        _writeable_config_modified.set()
    gc_keys = GuildConfig().get_dict().keys()
    for guild_id, config in guild_configs.items():
        if not gc_keys <= config.keys():
            _guild_config_modified.set()
            break

    # start config monitoring+upload threads
    if _guild_sync_thread is None:
        _guild_sync_thread = threading.Thread(target=_guild_config_sync_thread, daemon=True)
        _guild_sync_thread.start()
    if _writeable_sync_thread is None:
        _writeable_sync_thread = threading.Thread(target=_writeable_config_sync_thread, daemon=True)
        _writeable_sync_thread.start()


def _fetch_config(s3_obj, friendly_name):
    logger.info(f"Fetching {friendly_name}")
    try:
        with io.BytesIO() as f:
            s3_obj.download_fileobj(f)
            response_json = bytes.decode(f.getvalue())
        return json.loads(response_json)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            logger.info(f"Creating new {friendly_name}")
            _write_config(s3_obj, friendly_name, "{}")
            return {}
        else:
            raise
    except Exception:
        logger.error(f"Error fetching {friendly_name}")
        raise


def _write_config(s3_obj, friendly_name, content: str):
    logger.info(f"Uploading {friendly_name}")
    try:
        with io.BytesIO(str.encode(content)) as f:
            s3_obj.upload_fileobj(f)
        logger.info(f"Uploaded {friendly_name}")
    except Exception as e:
        logger.error(f"Error uploading {friendly_name}")
        raise e


def _writeable_config_sync_thread():
    while True:
        _writeable_config_modified.wait()
        _writeable_config_modified.clear()
        _write_config(s3_writeable_object, "writeable config", json.dumps(writeable_config_cache.get_dict()))
        time.sleep(5)


def _guild_config_sync_thread():
    while True:
        _guild_config_modified.wait()
        _guild_config_modified.clear()
        _write_config(s3_guild_object, "guild configs", json.dumps(guild_config_cache, default=Config.get_dict))
        time.sleep(5)
