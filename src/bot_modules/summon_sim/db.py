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


def _get_showcase_info(cursor: sqlite3.Cursor, channel_id: int, user_id: int) -> (core.SimShowcase, int, int):
    cursor.execute(
        "SELECT showcase, rate, total_summons FROM pity WHERE channel = ? AND user = ?",
        (channel_id, user_id)
    )
    result = cursor.fetchone()
    if result is None:
        return core.SimShowcaseCache.default_showcase, 0, 0
    else:
        return core.SimShowcaseCache.get(result[0]), result[1], result[2]


def _set_showcase_info(
        cursor: sqlite3.Cursor,
        channel_id: int,
        user_id: int,
        sim_showcase: core.SimShowcase,
        pity_progress: int,
        total_summons: int):
    cursor.execute(
        "INSERT OR REPLACE INTO pity VALUES (?, ?, ?, ?, ?)",
        (channel_id, user_id, pity_progress, sim_showcase.showcase.name, total_summons)
    )


def create_db():
    with get_cursor(pity_file) as cursor:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS pity ("
            "channel INTEGER,"
            "user INTEGER,"
            "rate INTEGER,"
            "showcase TEXT,"
            "total_summons INTEGER,"
            "PRIMARY KEY (channel, user))")


def set_showcase(channel_id: int, user_id: int, sim_showcase: core.SimShowcase):
    _check_session(channel_id, user_id)
    with get_cursor(pity_file) as cursor:
        _set_showcase_info(cursor, channel_id, user_id, sim_showcase, 0, 0)
    showcase_name = sim_showcase.showcase.name if sim_showcase.showcase.name != "none" else "a generic showcase"
    return f"Now summoning on {showcase_name}. Your 5★ rate and wyrmite counter have been reset."


def _get_showcase_explanation_string(
        sim_showcase: core.SimShowcase,
        pity_progress: int,
        total_summons: int,
        is_after_summon: bool):
    rate = sim_showcase.FIVE_STAR_RATE_TOTAL + sim_showcase.get_pity_percent(pity_progress)
    if is_after_summon:
        output_text = f"The 5★ rate is now {rate}%. "
    else:
        output_text = f"Your 5★ rate is {rate}%. "

    if pity_progress >= sim_showcase.PITY_PROGRESS_MAX:
        output_text += f"Your next summon is guaranteed to contain a 5★. "
    else:
        remaining = ((-pity_progress - 1) % 10) + 1
        output_text += f"{remaining} more summon{'s' if remaining > 1 else ''} until the 5★ rate increases. "

    return output_text + f"{total_summons * 120:,} wyrmite spent so far."


def get_current_showcase_info(channel_id: int, user_id: int):
    _check_session(channel_id, user_id)
    with get_cursor(pity_file) as cursor:
        sim_showcase, pity_progress, total_summons = _get_showcase_info(cursor, channel_id, user_id)
    showcase_name = sim_showcase.showcase.name if sim_showcase.showcase.name != "none" else "a generic showcase"
    rate_explanation = _get_showcase_explanation_string(sim_showcase, pity_progress, total_summons, False)
    return f"Currently summoning on {showcase_name}. " + rate_explanation, sim_showcase


def get_rate_breakdown(channel_id: int, user_id: int):
    _check_session(channel_id, user_id)
    with get_cursor(pity_file) as cursor:
        sim_showcase, pity_progress, total_summons = _get_showcase_info(cursor, channel_id, user_id)
    return sim_showcase.get_rates(pity_progress).get_breakdown()


def perform_summon(channel_id: int, user_id: int, is_tenfold: bool):
    _check_session(channel_id, user_id)
    with get_cursor(pity_file) as cursor:
        sim_showcase, pity_progress, total_summons = _get_showcase_info(cursor, channel_id, user_id)
        summon_func = sim_showcase.perform_tenfold if is_tenfold else sim_showcase.perform_solo
        summon_results, new_pity_progress = summon_func(pity_progress)
        new_total_summons = total_summons + (10 if is_tenfold else 1)
        _set_showcase_info(cursor, channel_id, user_id, sim_showcase, new_pity_progress, new_total_summons)

    return summon_results, _get_showcase_explanation_string(sim_showcase, new_pity_progress, new_total_summons, True)
