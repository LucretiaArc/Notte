import datetime
import asyncio
import logging
import config
from hook import Hook


logger = logging.getLogger(__name__)


def schedule_at_time(method, hour, minute=0, second=0, microsecond=0):
    """
    Schedules the provided synchronous method for the next occurrence of the given UTC wall clock time. e.g. if hour=14,
    minute=30, second=24, the method will be scheduled to run the next time it is 14:30:24 UTC. If the next occurrence
    is to be within 100ms, the method will be scheduled for the next day.
    :param method: the method to schedule
    :param hour: hour at which to call the method
    :param minute: minute at which to call the method
    :param second: second at which to call the method
    :param microsecond: microsecond at which to call the method
    """
    utc_now = datetime.datetime.utcnow()
    utc_next = utc_now.replace(hour=hour, minute=minute, second=second, microsecond=microsecond)
    time_delta = ((utc_next - utc_now).total_seconds() - 0.1) % 86400 + 0.1  # add 100ms safety
    asyncio.get_event_loop().call_later(time_delta, method)


def get_reset_day():
    """
    Returns the weekday of the most recent reset.
    :return: The weekday of the most recent reset, from 0 to 6. 0 is Monday, 6 is Sunday.
    """
    utc_now = datetime.datetime.utcnow()
    utc_today_reset = utc_now.replace(hour=6, minute=0, second=0, microsecond=0)
    return (utc_now.weekday() - (1 if utc_now < utc_today_reset else 0)) % 7


def create_daily_hook(name, hour, minute=0, second=0):
    """
    Schedules a new hook to be called at the same time every day. Time is given in UTC timezone.
    :param name: name of the hook to be scheduled
    :param hour: hour at which to call the hook
    :param minute: minute at which to call the hook
    :param second: second at which to call the hook
    """

    scheduled_hook = Hook.get(name)

    def scheduled_call():
        logger.info("Running scheduled hook " + name)
        asyncio.ensure_future(scheduled_hook())
        schedule_at_time(scheduled_call, hour, minute, second)

    schedule_at_time(scheduled_call, hour, minute, second)


def get_emote(name) -> str:
    """
    Gets the emote string for the given emote name
    :param name: name of the emote
    :return: emote string for the given name
    """
    emote_map = config.get_global_config()["emotes"]
    return emote_map[name] if name in emote_map else ""


def readable_list(items, last_separator="and") -> str:
    """
    Formats a list of strings to fit in an english sentence. For example:
    ["a"] -> "a"
    ["a", "b'] -> "a and b"
    ["a", "b", "c", "d"] -> "a, b, c, and d"
    :param items: list of items to turn into an english list.
    :param last_separator: separator word to use before the last item. This is "and" in the above examples.
    :return: string representing the list of items
    """
    if len(items) < 3:
        return (" " + last_separator + " ").join(items)

    return ", ".join(items[:-1]) + ", " + last_separator + " " + items[-1]


def safe_int(value, default):
    """
    Attempts a cast to int, returning a default value if the cast fails.
    :param value: value to cast
    :param default: default value
    :return: result of cast or default value
    """
    try:
        return int(value)
    except ValueError:
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
        return not message.channel.is_private and message.author.server_permissions.manage_server
    elif level == "owner":
        return message.author.id == config.get_global_config()["owner_id"]
