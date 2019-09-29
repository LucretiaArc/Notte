import typing
import aiohttp
import itertools
import util
import abc
import datetime
import string
import discord
import logging
import _string

logger = logging.getLogger(__name__)


class Entity(abc.ABC):
    __initialised = False

    @classmethod
    @abc.abstractmethod
    def init(cls):
        pass

    @abc.abstractmethod
    def get_key(self) -> str:
        """
        :return: the key representing this entity in a repository.
        """
        return ""

    @abc.abstractmethod
    def get_embed(self) -> discord.Embed:
        """
        :return: A discord.Embed representing the entity.
        """
        return discord.Embed()

    @classmethod
    @abc.abstractmethod
    def get_all(cls) -> dict:
        """
        Returns a dict representing the repository for this entity type.
        :return:
        """
        return {}

    @classmethod
    @abc.abstractmethod
    def find(cls, key: str):
        """
        Finds the entity for a given key.
        :param key: key of the entity to find (as returned by get_key)
        :return: entity for the given key, or None  if it was not found.
        """
        return None

    def __repr__(self):
        return str(vars(self))

    @abc.abstractmethod
    def __str__(self):
        return "Undefined Entity"


class EntityMapper:
    """
    Maps data from a dictionary to an Entity based on a set configuration.
    """
    def __init__(self, target_class: typing.Type[Entity]):
        self.inst_class = target_class
        self.inst_map_funcs = {}
        self.inst_map_arg_keys = {}
        self.post_processor = None

    def add_property(self, attr_name, cast_function: typing.Callable, *args: str):
        """
        Adds a property to be mapped. If attr_name is None, then the property will be mapped to an added attribute,
        entity.POST_PROCESS, which can be deleted later.
        :param attr_name: name of attribute to map to, or None if the property is a post-process attribute
        :param cast_function: function to use to transform the data before assigning it to the attribute
        :param args: names of the data fields whose values should be passed to the cast function. Often, this is just
        the name of the data field to be mapped. Not applied to post-process attributes, which are added directly to the
        POST_PROCESS attribute dictionary.
        """
        self.inst_map_funcs[attr_name] = cast_function
        self.inst_map_arg_keys[attr_name] = args

    def map(self, entity_data: dict):
        inst = self.inst_class()

        for attr_name, map_func in self.inst_map_funcs.items():
            if attr_name is not None:
                if not hasattr(inst, attr_name):
                    raise AttributeError(f"Invalid entity attribute: {attr_name}")

                args = list(map(entity_data.get, self.inst_map_arg_keys[attr_name]))
                if None in args:
                    invalid_key = self.inst_map_arg_keys[attr_name][args.index(None)]
                    raise KeyError(f"Invalid data key: {invalid_key}")

                try:
                    value = map_func(*args)
                except Exception:
                    logger.exception(f'Exception encountered while processing attribute "{attr_name}" with args {args}:')
                    value = None

                setattr(inst, attr_name, value)
            else:
                post_process = {}
                for pp_attr_name in self.inst_map_arg_keys[None]:
                    post_process[pp_attr_name] = entity_data.get(pp_attr_name)
                setattr(inst, "POST_PROCESS", post_process)

        if not inst.get_key():
            return None

        if self.post_processor:
            # post-process instance, if post processor returns falsey value then instance is invalid so return None
            if not self.post_processor(inst):
                return None

        return inst

    # mapping helper methods
    @staticmethod
    def none(s: str):
        return s

    @staticmethod
    def text(s: str):
        return util.clean_wikitext(s) or None

    @staticmethod
    def int(s: str):
        return util.safe_int(s, None)

    @staticmethod
    def date(s: str):
        if not s:
            return None

        dt = datetime.datetime.strptime(s + " +0000", "%Y-%m-%d %H:%M:%S %z")
        return dt if 1970 < dt.year < 2100 else None

    @staticmethod
    def sum(*args: str):
        try:
            return sum(EntityMapper.int(s) for s in args)
        except TypeError:
            return None

    @staticmethod
    def filtered_list_of(mapping_function: typing.Callable):
        return lambda *args: list(filter(None, [mapping_function(s) for s in args]))


class EntityRepository:
    """
    Stores and updates a particular type of entity using an EntityMapper
    """
    def __init__(self, mapper: EntityMapper, table_name: str):
        self.table_name = table_name
        self.entity_mapper = mapper
        self.data = {}
        self.post_processor = None

    def get_query_url(self, limit: int, offset: int):
        base_url = "https://dragalialost.gamepedia.com/api.php?"
        table_fields = ",".join(set(itertools.chain(*self.entity_mapper.inst_map_arg_keys.values())))
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

        if self.post_processor:
            self.post_processor(data_new)

        self.data = data_new

    def get_from_key(self, key):
        return self.data.get(key)


class EmbedFormatter(string.Formatter):
    """
    Custom string.Formatter which handles navigation exceptions, supports negative list indices, and supports
    a different set of conversions. The originally provided r, s, and a conversions are not available.
    """

    def __init__(self, default="?"):
        self.conversions = {}
        self.default = default

    def add_conversion(self, conversion, function):
        if conversion not in self.conversions:
            self.conversions[conversion] = function
        else:
            raise ValueError(f'Conversion already exists for key "{conversion}"')

    def get_field(self, field_name, args, kwargs):
        # This is a modified version of the existing implementation of get_field, as defined in string.Formatter.
        # It supports negative list indices, and ignores navigation exceptions in favour of returning None.
        # Only the former requires modification of this method.
        first, rest = _string.formatter_field_name_split(field_name)

        obj = self.get_value(first, args, kwargs)

        try:
            for is_attr, i in rest:
                if is_attr:
                    obj = getattr(obj, i)
                else:
                    v = i
                    if isinstance(i, str):
                        v = util.safe_int(i, None) or v

                    obj = obj[v]
        except (AttributeError, TypeError, IndexError):
            return None, field_name

        return obj, first

    def format_field(self, value, spec):
        if value is None:
            return self.default

        return super().format_field(value, spec)

    def convert_field(self, value, conversion):
        if conversion is None:  # no conversion
            return value if value else self.default
        elif conversion == "r":  # rarity emote
            return util.get_emote(f"rarity{value}")
        elif conversion == "e":  # generic emote
            return util.get_emote(value)
        elif conversion == "d":  # date string from datetime
            return value.date().isoformat() if value else self.default
        elif conversion == "o":  # optional value, with newline if present
            return f"\n{value}" if value else ""
        elif conversion == "l":  # length of value
            return len(value) if value else self.default
        else:
            raise ValueError(f"Unknown conversion specifier {conversion}")
