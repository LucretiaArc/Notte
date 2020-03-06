import logging
import urllib.parse
import config
import io
import discord
import sys
import pathlib


logger = logging.getLogger(__name__)


def get_emote(name) -> str:
    """
    Gets the emote string for the given emote name. Emote names are case-insensitive.
    An object may be passed in as an emote, where str(name) will be used as the name of the emote.
    :param name: name of the emote
    :return: emote string for the given name
    """
    name = str(name).lower()
    emote_map = config.get_global("emotes")
    return emote_map[name] if name in emote_map else ""


def safe_int(value, default):
    """
    Attempts a cast to int, returning a default value if the cast fails.
    :param value: value to cast
    :param default: default value
    :return: result of cast or default value
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def check_command_permissions(message, level) -> bool:
    """
    Determines whether a command of the given level can be used, given the context of a sent message.
    :param message: context message used to determine whether the command can be used
    :param level: level of command to use, may be one of "public", "admin", or "owner"
    :return: True if the command can be used, False otherwise
    """
    if level == "public":
        return True
    elif level == "admin":
        return isinstance(message.channel, discord.abc.GuildChannel) and message.author.guild_permissions.manage_guild
    elif level == "owner":
        return message.author.id == config.get_global("general")["owner_id"]


def get_link(page_name):
    """
    Return a link to the wiki for the given page name
    :param page_name: name of the page to link to
    :return: link to page
    """
    return "https://dragalialost.gamepedia.com/" + urllib.parse.quote(page_name.replace(" ", "_"))


async def send_long_message_as_file(channel: discord.abc.Messageable, msg: str, filename="message.txt"):
    """
    Sends a potentially-long message as a file if it exceeds the maximum message length.
    :param channel: channel to send the message in
    :param msg: message to send
    :param filename: filename to use
    """
    if len(msg) <= 2000:
        await channel.send(msg)
    else:
        await channel.send(file=discord.File(fp=io.BytesIO(bytes(msg, "UTF-8")), filename=filename))


def path(path_fragment):
    """
    Gets a full file path from a path fragment. Path fragments are relative to the top level of the project (the
    directory containing the "src" directory). Path fragments should not contain a leading slash.
    :param path_fragment: a path fragment
    :return: full file path
    """
    return str(pathlib.Path(sys.path[0]).parent / path_fragment)
