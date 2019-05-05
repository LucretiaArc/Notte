import typing
import aiohttp
import itertools
import mwparserfromhell
import html
import re
import util
from data._static import *
import data.abc


class EntityMapper:
    """
    Maps data from a dictionary to an Entity based on a set configuration.
    """
    def __init__(self, target_class: typing.Type[data.abc.Entity]):
        self.inst_class = target_class
        self.inst_map_funcs = {}
        self.inst_map_arg_keys = {}
        self.post_processor = None

    def add_property(self, attr_name: str, cast_function: typing.Callable, *args: str):
        self.inst_map_funcs[attr_name] = cast_function
        self.inst_map_arg_keys[attr_name] = args

    def set_post_processor(self, post_processor: typing.Callable):
        self.post_processor = post_processor

    def map(self, entity_data: dict):
        inst = self.inst_class()
        for attr_name, map_func in self.inst_map_funcs.items():
            if not hasattr(inst, attr_name):
                raise AttributeError("Invalid entity attribute: {0}".format(attr_name))

            args = list(map(entity_data.get, self.inst_map_arg_keys[attr_name]))
            if None in args:
                invalid_key = self.inst_map_arg_keys[attr_name][args.index(None)]
                raise KeyError("Invalid data key: {0}".format(invalid_key))

            value = map_func(*args)
            setattr(inst, attr_name, value)

        if self.post_processor:
            # process instance, if post processor returns falsey value then instance is invalid so return None
            if not self.post_processor(inst):
                return None

        return inst

    # mapping helper methods
    @staticmethod
    def none(s: str):
        return s

    @staticmethod
    def text(s: str):
        return clean_wikitext(s) or None

    @staticmethod
    def int(s: str):
        return util.safe_int(s, None)

    @staticmethod
    def date(s: str):
        return s if s and not s.startswith("1970") else None

    @staticmethod
    def weapon_type(s: str):
        wt_id = EntityMapper.int(s)
        return None if wt_id is None else WeaponType(wt_id)

    @staticmethod
    def element(s: str):
        el_id = EntityMapper.int(s)
        return None if el_id not in range(1, 6) else Element(el_id)

    @staticmethod
    def dragon_gift(s: str):
        gift_id = EntityMapper.int(s)
        return None if gift_id not in range(1, 8) else DragonGift(gift_id)

    @staticmethod
    def sum(*args: str):
        try:
            return sum(EntityMapper.int(s) for s in args)
        except TypeError:
            return None

    @staticmethod
    def filtered_list_of(mapping_function: typing.Callable):
        return lambda *args: filter(None, [mapping_function(s) for s in args])


class EntityRepository:
    """
    Stores and updates a particular type of entity using an EntityMapper
    """
    def __init__(self, mapper: EntityMapper, table_name: str):
        self.table_name = table_name
        self.entity_mapper = mapper
        self.data = {}

    def get_query_url(self, limit: int, offset: int):
        base_url = "https://dragalialost.gamepedia.com/api.php?"
        table_fields = ",".join(itertools.chain(*self.entity_mapper.inst_map_arg_keys.values()))
        params = {
            "action": "cargoquery",
            "format": "json",
            "tables": self.table_name,
            "fields": table_fields,
            "order_by": "",
            "limit": str(limit),
            "offset": str(offset)
        }

        return base_url + "&".join(k+"="+v for k, v in params.items())

    async def process_query(self, session: aiohttp.ClientSession, limit=500):
        """
        Retrieves the results for this parser's json cargo query, which may be split across multiple queries due to a
        result limit.
        :param session: aiohttp.ClientSession to use for the requests
        :param limit: result limit for each request
        :return: list of result entries
        """

        offset = 0
        result_items = []
        while True:
            async with session.get(self.get_query_url(limit, offset)) as response:
                result_json = await response.json()
                inner_result_list = result_json["cargoquery"]
                query_items = [d["title"] for d in inner_result_list]
                result_items += query_items
                offset += limit

                if len(query_items) < limit or len(inner_result_list) == 0:
                    return result_items

    async def update_data(self, session: aiohttp.ClientSession):
        query_data = await self.process_query(session)

        data_new = {}
        for e in query_data:
            entity = self.entity_mapper.map(e)
            if entity:
                data_new[entity.get_key()] = entity

        self.data = data_new


def clean_wikitext(wikitext):
    """
    Applies several transformations to wikitext, so that it's suitable for display in a message. This function does NOT
    sanitise the input, so the output of this method isn't safe for use in a HTML document. This method, in no
    particular order:
     - Strips spaces from the ends
     - Strips wikicode
     - Decodes HTML entities then strips HTML tags
     - Reduces consecutive spaces
    :param wikitext: wikitext to strip
    :return: string representing the stripped wikitext
    """
    html_removed = re.sub(r"(<[^<]+?>)", "", html.unescape(wikitext))
    wikicode_removed = mwparserfromhell.parse(html_removed).strip_code()
    spaces_reduced = re.sub(r" {2,}", " ", wikicode_removed)
    return spaces_reduced.strip()
