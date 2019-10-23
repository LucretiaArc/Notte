import glob
import importlib
from os.path import dirname, basename, isfile

import logging
logger = logging.getLogger(__name__)


def import_modules():
    modules = glob.glob(dirname(__file__) + "/*.py")
    module_names = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
    for m in module_names:
        # noinspection PyBroadException
        try:
            importlib.import_module("."+m, package="bot_modules")
        except Exception:
            logger.exception(f'Error while importing module "{m}"')


# Standard events:
# on_init(client:discord.Client)
# on_ready()
# on_guild_join(guild:discord.Guild)
# on_message(message:discord.Message)
# on_message_private(message:discord.Message)
# on_mention(message:discord.Message)
# on_reset()
# before_reset()
# download_data()
# data_downloaded()
#
# Command events:
# public!COMMAND(message:discord.Message, args:string)
# admin!COMMAND(message:discord.Message, args:string)
# owner!COMMAND(message:discord.Message, args:string)
