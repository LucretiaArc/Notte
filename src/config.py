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
    Represents the bot configuration, including both global and server configurations.
    Global and server configs are provided as mapping proxies (usable as immutable dictionaries).
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
            logger.info("Uploading modified server config")
            cls.__sc_object.put(Body=json.dumps(cls.__sc))
            logger.info("Server config synchronised")
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

        logger.info("Fetching server configs")
        # get server configs from S3 bucket
        cls.__sc = json.load(cls.__sc_object.get()["Body"])

        logger.info("Starting configuration synchronisation thread.")
        cls.__sc_sync_thread = threading.Thread(target=cls.__config_sync_thread)
        cls.__sc_sync_thread.start()

        logger.info("Configuration loaded.")

    # global config
    @classmethod
    def get_global_config(cls):
        return cls.__gc

    # server config
    @classmethod
    def set_server_config(cls, server_id: str, new_config: dict):
        logger.info("Setting server config for " + str(server_id))
        if server_id not in cls.__sc:
            cls.__sc[server_id] = {}

        cls.__sc[server_id].clear()
        cls.__sc[server_id].update(new_config)
        cls.__sc_modified.set()

    @classmethod
    def get_server_config(cls, server_id: str):
        if server_id not in cls.__sc:
            cls.set_server_config(server_id, {
                "token": "!!",
                "active_channel": ""
            })

        return types.MappingProxyType(cls.__sc[server_id])

    @classmethod
    def inspect_server_configs(cls):
        return copy.deepcopy(cls.__sc)


# common shortcuts
get_global_config = Config.get_global_config
get_server_config = Config.get_server_config
set_server_config = Config.set_server_config


def get_response_token(server: discord.server):
    return get_server_config(server.id)["token"] if server else "!!"
