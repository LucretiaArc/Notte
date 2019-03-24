import json
import types
import boto3
import os
import discord
import copy
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Config:
    """
    Represents the bot configuration, including both global and server configurations.
    Global and server configs are provided as mapping proxies (usable as immutable dictionaries).
    """
    __global_config = None
    __server_configs = None
    __server_config_object = boto3.resource('s3').Object("cloud-cube", os.environ["SERVER_CONFIG_KEY"])

    @classmethod
    def init_configuration(cls):
        """
        Retrieves and loads configuration from local and remote sources.
        """
        logger.info("Retrieving local config")
        # get global config from file
        with open("global-config.json") as file:
            cls.__global_config = types.MappingProxyType(json.load(file))

        logger.info("Fetching server configs")
        # get server configs from S3 bucket
        cls.__server_configs = json.load(cls.__server_config_object.get()["Body"])

        logger.info("Configuration loaded.")

    # global config
    @classmethod
    def get_global_config(cls):
        return cls.__global_config

    # server config
    @classmethod
    def __upload_server_configs(cls):
        logger.info("Uploading server configs")
        cls.__server_config_object.put(Body=json.dumps(cls.__server_configs))

    @classmethod
    def set_server_config(cls, server_id: str, new_config: dict):
        logger.info("Setting server configs for " + str(server_id))
        if server_id not in cls.__server_configs:
            cls.__server_configs[server_id] = {}

        cls.__server_configs[server_id].clear()
        cls.__server_configs[server_id].update(new_config)
        cls.__upload_server_configs()

    @classmethod
    def get_server_config(cls, server_id: str):
        if server_id not in cls.__server_configs:
            cls.set_server_config(server_id, {
                "token": "!!",
                "active_channel": ""
            })

        return types.MappingProxyType(cls.__server_configs[server_id])

    @classmethod
    def inspect_server_configs(cls):
        return copy.deepcopy(cls.__server_configs)


# common shortcuts
get_global_config = Config.get_global_config
get_server_config = Config.get_server_config
set_server_config = Config.set_server_config


def get_response_token(server: discord.server):
    return get_server_config(server.id)["token"] if server else "!!"
