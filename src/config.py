import json
import types
import boto3
import os
import discord
import threading
import copy
import logging
import time

logger = logging.getLogger(__name__)


class Config:
    """
    Represents the bot configuration, including static global, guild, and writeable global configurations.
    Global and guild configs are provided as mapping proxies (usable as immutable dictionaries).
    """
    __gc = None
    __sc = None
    __wc = None
    __sc_object = boto3.resource('s3').Object("cloud-cube", os.environ["SERVER_CONFIG_KEY"])
    __wc_object = boto3.resource('s3').Object("cloud-cube", os.environ["GLOBAL_CONFIG_KEY"])
    __config_modified = threading.Event()
    __sync_thread = None

    sc_default = {
        "token": "!!",
        "active_channel": 0
    }

    wc_default = {
        "news_last_priority": 411
    }

    @classmethod
    def __config_sync_thread(cls):
        while True:
            cls.__config_modified.wait()
            cls.__config_modified.clear()
            logger.info("Uploading guild and writeable config")
            cls.__sc_object.put(Body=json.dumps(cls.__sc))
            cls.__wc_object.put(Body=json.dumps(cls.__wc))
            logger.info("Guild/writeable config synchronised")
            time.sleep(5)  # won't synchronise for the next 5 seconds

    @classmethod
    def init_configuration(cls):
        """
        Retrieves and loads configuration from local and remote sources.
        """
        if cls.__sync_thread is not None:
            logger.warning("Configuration already initialised, but initialisation attempted again")
            return

        logger.info("Retrieving local config")
        # get global config from file
        with open("global-config.json") as file:
            cls.__gc = types.MappingProxyType(json.load(file))

        logger.info("Fetching guild configs")
        # get guild configs from S3 bucket
        guild_configs = json.load(cls.__sc_object.get()["Body"])
        cls.__sc = {}
        sc_key_list = cls.sc_default.keys()
        for gid, gconfig in guild_configs.items():
            if gconfig.keys() != sc_key_list:
                cls.__sc[gid] = cls.sc_default.copy()
                cls.__sc[gid].update(gconfig)
                cls.__config_modified.set()
            else:
                cls.__sc[gid] = gconfig

        logger.info("Fetching writeable config")
        # get writeable config from S3 bucket
        wconfig = json.load(cls.__wc_object.get()["Body"])
        cls.__wc = {}
        if wconfig.keys() != cls.wc_default.keys():
            cls.__wc = cls.wc_default.copy()
            cls.__wc.update(wconfig)
            cls.__config_modified.set()
        else:
            cls.__wc = wconfig

        logger.info("Starting configuration synchronisation thread.")
        cls.__sync_thread = threading.Thread(target=cls.__config_sync_thread)
        cls.__sync_thread.start()

        logger.info("Configuration loaded.")

    # global config
    @classmethod
    def get_global_config(cls):
        return cls.__gc

    # guild config
    @classmethod
    def set_guild_config(cls, guild: discord.Guild, new_config: dict):
        logger.info("Setting guild config for " + str(guild.id))
        if str(guild.id) not in cls.__sc:
            cls.__sc[str(guild.id)] = {}

        cls.__sc[str(guild.id)].clear()
        cls.__sc[str(guild.id)].update(new_config)
        cls.__config_modified.set()

    @classmethod
    def get_guild_config(cls, guild: discord.Guild):
        if str(guild.id) not in cls.__sc:
            cls.set_guild_config(guild, cls.sc_default)

        return types.MappingProxyType(cls.__sc[str(guild.id)])

    @classmethod
    def get_guild_config_editable(cls, guild: discord.Guild):
        if str(guild.id) not in cls.__sc:
            cls.set_guild_config(guild, cls.sc_default)

        return copy.deepcopy(cls.__sc[str(guild.id)])

    @classmethod
    def set_writeable_config(cls, new_config: dict):
        logger.info("Setting writeable config")

        cls.__wc.clear()
        cls.__wc.update(new_config)
        cls.__config_modified.set()

    @classmethod
    def get_writeable_config(cls):
        return copy.deepcopy(cls.__wc)

    @classmethod
    def inspect_guild_configs(cls):
        return copy.deepcopy(cls.__sc)


# common shortcuts
get_global_config = Config.get_global_config
get_guild_config = Config.get_guild_config
get_guild_config_editable = Config.get_guild_config_editable
set_guild_config = Config.set_guild_config
get_wglobal_config = Config.get_writeable_config
set_wglobal_config = Config.set_writeable_config


def get_prefix(guild: discord.Guild):
    return get_guild_config(guild)["token"] if guild else "!!"
