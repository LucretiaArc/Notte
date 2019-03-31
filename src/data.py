import aiohttp
import util
import logging
from enum import Enum
from aenum import MultiValueEnum

logger = logging.getLogger(__name__)


async def update_repositories():
    async with aiohttp.ClientSession() as session:
        logger.info("Updating adventurer repository")
        await Adventurer.update_repository(session)
        logger.info("Updated adventurer repository")


class Element(MultiValueEnum):
    FIRE = 1, "Flame"
    WATER = 2, "Water"
    WIND = 3, "Wind"
    LIGHT = 4, "Light"
    DARK = 5, "Shadow"

    def __str__(self):
        return self.name.capitalize()


class WeaponType(Enum):
    SWORD = 1
    BLADE = 2
    DAGGER = 3
    AXE = 4
    LANCE = 5
    BOW = 6
    WAND = 7
    STAFF = 8

    def __str__(self):
        return self.name.capitalize()


class Adventurer:
    """
    Represents an adventurer and some of their associated data
    """
    adventurers = {}

    @classmethod
    async def update_repository(cls, session: aiohttp.ClientSession):
        url = "https://dragalialost.gamepedia.com/api.php?action=cargoquery&tables=Adventurers&format=json&limit=500&fields=" \
              "Id,FullName,Name,Title,Description,Obtain,DATE(ReleaseDate)%3DReleaseDate," \
              "WeaponTypeId,ElementalTypeId,Rarity," \
              "MaxHp,PlusHp0,PlusHp1,PlusHp2,PlusHp3,PlusHp4,McFullBonusHp5," \
              "MaxAtk,PlusAtk0,PlusAtk1,PlusAtk2,PlusAtk3,PlusAtk4,McFullBonusAtk5," \
              "Skill1Name,Skill2Name," \
              "Abilities11,Abilities12,Abilities13,Abilities14," \
              "Abilities21,Abilities22,Abilities23,Abilities24," \
              "Abilities31,Abilities32,Abilities33,Abilities34," \
              "ExAbilityData1,ExAbilityData2,ExAbilityData3,ExAbilityData4,ExAbilityData5"

        async with session.get(url) as response:
            adventurer_json = await response.json()
            adventurer_info_list = [a["title"] for a in adventurer_json["cargoquery"]]

            adventurers_new = {}

            safe_int = util.safe_int
            for a in adventurer_info_list:

                adv_id = a["Id"] or None
                if adv_id is None:
                    continue

                adv = cls(adv_id)

                # basic info
                adv.full_name = a["FullName"] or None
                adv.name = a["Name"] or None
                adv.title = a["Title"] or None
                adv.description = a["Description"] or None
                adv.obtained = a["Obtain"].replace("[[", "").replace("]]", "") or None
                adv.release_date = a["ReleaseDate"] or None
                wt_id = safe_int(a["WeaponTypeId"], None)
                adv.weapon_type = None if wt_id is None else WeaponType(wt_id)
                el_id = safe_int(a["ElementalTypeId"], None)
                adv.element = None if el_id is None else Element(el_id)
                adv.rarity = safe_int(a["Rarity"], None)

                # max hp calculation
                max_hp_vals = [
                    safe_int(a["MaxHp"], None),
                    safe_int(a["PlusHp0"], None),
                    safe_int(a["PlusHp1"], None),
                    safe_int(a["PlusHp2"], None),
                    safe_int(a["PlusHp3"], None),
                    safe_int(a["PlusHp4"], None),
                    safe_int(a["McFullBonusHp5"], None),
                ]
                try:
                    adv.max_hp = sum(max_hp_vals)
                except TypeError:
                    adv.max_hp = None

                # max strength calculation
                max_str_vals = [
                    safe_int(a["MaxAtk"], None),
                    safe_int(a["PlusAtk0"], None),
                    safe_int(a["PlusAtk1"], None),
                    safe_int(a["PlusAtk2"], None),
                    safe_int(a["PlusAtk3"], None),
                    safe_int(a["PlusAtk4"], None),
                    safe_int(a["McFullBonusAtk5"], None),
                ]
                try:
                    adv.max_str = sum(max_str_vals)
                except TypeError:
                    adv.max_str = None

                # TODO: max might, skills, abilities, coability

                adventurers_new[adv_id] = adv

            cls.adventurers = adventurers_new

    def __init__(self, id_str: str):
        self.id_str = id_str
        self.full_name = ""
        self.name = ""
        self.title = ""
        self.description = ""
        self.obtained = ""
        self.release_date = ""
        self.weapon_type = None
        self.rarity = 0
        self.element = None
        self.max_hp = 0
        self.max_str = 0
        self.max_might = 0

        # list of IDs
        self.skill_1 = []
        self.skill_2 = []
        self.ability_1 = []
        self.ability_2 = []
        self.ability_3 = []
        self.coability = []
