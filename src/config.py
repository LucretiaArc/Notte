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
    Represents the bot configuration, including both global and guild configurations.
    Global and guild configs are provided as mapping proxies (usable as immutable dictionaries).
    """
    __gc = None
    __sc = None
    __sc_object = boto3.resource('s3').Object("cloud-cube", os.environ["SERVER_CONFIG_KEY"])
    __sc_modified = threading.Event()
    __sc_sync_thread = None

    @classmethod
    def __config_sync_thread(cls):
        while True:
            cls.__sc_modified.wait()
            cls.__sc_modified.clear()
            logger.info("Uploading modified guild config")
            cls.__sc_object.put(Body=json.dumps(cls.__sc))
            logger.info("Guild config synchronised")
            time.sleep(5)  # won't synchronise for the next 5 seconds

    @classmethod
    def init_configuration(cls):
        """
        Retrieves and loads configuration from local and remote sources.
        """
        if cls.__sc_sync_thread is not None:
            logger.warning("Configuration already initialised, but initialisation attempted again")
            return

        logger.info("Retrieving local config")
        # get global config from file
        with open("global-config.json") as file:
            cls.__gc = types.MappingProxyType(json.load(file))

        logger.info("Fetching guild configs")
        # get guild configs from S3 bucket
        guild_configs = json.load(cls.__sc_object.get()["Body"])
        cls.__sc = dict((int(k), v) for k, v in guild_configs.items())  # convert guild IDs to int

        logger.info("Starting configuration synchronisation thread.")
        cls.__sc_sync_thread = threading.Thread(target=cls.__config_sync_thread)
        cls.__sc_sync_thread.start()

        logger.info("Configuration loaded.")

    # global config
    @classmethod
    def get_global_config(cls):
        return cls.__gc

    # guild config
    @classmethod
    def set_guild_config(cls, guild: discord.Guild, new_config: dict):
        logger.info("Setting guild config for " + str(guild.id))
        if guild.id not in cls.__sc:
            cls.__sc[guild.id] = {}

        cls.__sc[guild.id].clear()
        cls.__sc[guild.id].update(new_config)
        cls.__sc_modified.set()

    @classmethod
    def get_guild_config(cls, guild: discord.Guild):
        if guild.id not in cls.__sc:
            cls.set_guild_config(guild, {
                "token": "!!",
                "active_channel": 0
            })

        return types.MappingProxyType(cls.__sc[guild.id])

    @classmethod
    def get_guild_config_editable(cls, guild: discord.Guild):
        if guild.id not in cls.__sc:
            cls.set_guild_config(guild, {
                "token": "!!",
                "active_channel": 0
            })

        return copy.deepcopy(cls.__sc[guild.id])

    @classmethod
    def inspect_guild_configs(cls):
        return copy.deepcopy(cls.__sc)


# common shortcuts
get_global_config = Config.get_global_config
get_guild_config = Config.get_guild_config
get_guild_config_editable = Config.get_guild_config_editable
set_guild_config = Config.set_guild_config


def get_prefix(guild: discord.Guild):
    return get_guild_config(guild)["token"] if guild else "!!"
