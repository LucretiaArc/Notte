import datetime
import asyncio
import logging
from hook import Hook


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def schedule_at_time(method, hour, minute=0, second=0, microsecond=0):
    """
    Schedules the provided synchronous method for the next occurrence of the given UTC wall clock time. e.g. if hour=14,
    minute=30, second=24, the method will be scheduled to run the next time it is 14:30:24 UTC. If the next occurrence
    is to be within 10ms, the method will be scheduled for the next day.
    :param method: the method to schedule
    :param hour: hour at which to call the method
    :param minute: minute at which to call the method
    :param second: second at which to call the method
    :param microsecond: microsecond at which to call the method
    :return:
    """
    utc_now = datetime.datetime.utcnow()
    utc_next = utc_now.replace(hour=hour, minute=minute, second=second, microsecond=microsecond)
    time_delta = ((utc_next - utc_now).total_seconds() - 0.01) % 86400 + 0.01  # add 10ms safety
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


def get_emote(config, name):
    """
    Gets the emote string for the given emote name
    :param config: configuration settings to use for finding the emote
    :param name: name of the emote
    :return: emote string for the given name
    """
    if name in config["emotes"]:
        return config["emotes"][name]

    return ""
