import aiohttp
import logging
import hook

from data import abc
from ._static import Element, WeaponType, Resistance, DragonGift, get_rarity_colour
from ._entities import Adventurer, Dragon, Wyrmprint, Weapon, Skill, Ability, CoAbility

logger = logging.getLogger(__name__)


async def update_repositories():
    async with aiohttp.ClientSession() as session:
        logger.info("Updating skill repository")
        await Skill.repository.update_data(session)
        logger.info("Updating ability repository")
        await Ability.repository.update_data(session)
        logger.info("Updating coability repository")
        await CoAbility.repository.update_data(session)
        logger.info("Updating adventurer repository")
        await Adventurer.repository.update_data(session)
        logger.info("Updating dragon repository")
        await Dragon.repository.update_data(session)
        logger.info("Updating wyrmprint repository")
        await Wyrmprint.repository.update_data(session)
        logger.info("Updating weapon repository")
        await Weapon.repository.update_data(session)
        logger.info("Updated all repositories.")

    await hook.Hook.get("data_downloaded")()


hook.Hook.get("download_data").attach(update_repositories)
