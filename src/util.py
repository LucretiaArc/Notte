import datetime
import asyncio


async def schedule_at_time(method, hour, minute=0, second=0, microsecond=0):
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
