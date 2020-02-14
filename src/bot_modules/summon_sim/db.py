import sqlite3
import contextlib
import util
from . import core


pity_file = util.path("data/pity.db")


@contextlib.contextmanager
def get_cursor(path):
    with contextlib.closing(sqlite3.connect(path)) as connection:
        with connection:
            with contextlib.closing(connection.cursor()) as cursor:
                yield cursor


def _check_session(channel_id: int, user_id: int):
    if not channel_id or not user_id:
        raise ValueError(f"Invalid channel id '{channel_id}' or user id '{user_id}'")


def _get_showcase_info(cursor: sqlite3.Cursor, channel_id: int, user_id: int):
    cursor.execute(
        "SELECT showcase, rate FROM pity WHERE channel = ? AND user = ?",
        (channel_id, user_id)
    )
    result = cursor.fetchone()
    if result is None:
        return core.get_summonable_showcase("none"), 0
    else:
        return core.get_summonable_showcase(result[0]), result[1]


def _set_showcase_info(cursor: sqlite3.Cursor, channel_id: int, user_id: int, showcase: core.Showcase, pity_progress: int):
    cursor.execute(
        "INSERT OR REPLACE INTO pity VALUES (?, ?, ?, ?)",
        (channel_id, user_id, pity_progress, showcase.name)
    )


def create_db():
    with get_cursor(pity_file) as cursor:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS pity ("
            "channel INTEGER,"
            "user INTEGER,"
            "rate INTEGER,"
            "showcase TEXT,"
            "PRIMARY KEY (channel, user))")


def set_showcase(channel_id: int, user_id: int, showcase: core.Showcase):
    _check_session(channel_id, user_id)
    with get_cursor(pity_file) as cursor:
        _set_showcase_info(cursor, channel_id, user_id, showcase, 0)
    showcase_name = showcase.name if showcase.name != "none" else "a generic showcase"
    return f"Now summoning on {showcase_name}. Your 5★ rate has been reset."


def _get_rate_explanation_string(rate: float, remaining: int, after_summon: bool):
    if after_summon:
        current_rate_text = f"The 5★ rate is now {rate}%. "
    else:
        current_rate_text = f"Your 5★ rate is {rate}%. "

    if rate == 9:
        return current_rate_text + f"Your next summon is guaranteed to contain a 5★. "
    else:
        return current_rate_text + f"{remaining} more summon{'s' if remaining > 1 else ''} until the 5★ rate increases. "


def get_current_showcase_info(channel_id: int, user_id: int):
    _check_session(channel_id, user_id)
    with get_cursor(pity_file) as cursor:
        showcase, pity_progress = _get_showcase_info(cursor, channel_id, user_id)
    showcase_name = showcase.name if showcase.name != "none" else "a generic showcase"
    five_star_rate = showcase.get_five_star_rate(pity_progress)
    summons_left = core.get_summons_remaining(pity_progress)
    rate_explanation = _get_rate_explanation_string(five_star_rate, summons_left, False)
    return f"Currently summoning on {showcase_name}. " + rate_explanation, showcase


def perform_summon(channel_id: int, user_id: int, is_tenfold: bool):
    _check_session(channel_id, user_id)
    with get_cursor(pity_file) as cursor:
        showcase, pity_progress = _get_showcase_info(cursor, channel_id, user_id)
        summon_func = showcase.perform_tenfold if is_tenfold else showcase.perform_solo
        summon_results, new_pity_progress = summon_func(pity_progress)
        _set_showcase_info(cursor, channel_id, user_id, showcase, new_pity_progress)

    new_rate = showcase.get_five_star_rate(new_pity_progress)
    summons_left = core.get_summons_remaining(new_pity_progress)
    return summon_results, _get_rate_explanation_string(new_rate, summons_left, True)
