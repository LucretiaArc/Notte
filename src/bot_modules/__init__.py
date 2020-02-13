import importlib
import pathlib
import logging
logger = logging.getLogger(__name__)


def import_modules():
    this_file_path = pathlib.Path(__file__)
    for path in this_file_path.parent.iterdir():
        if path == this_file_path:
            continue
        if path.is_dir() and (path / "__init__.py").exists() or path.is_file() and path.suffix == ".py":
            # noinspection PyBroadException
            try:
                importlib.import_module(f".{path.stem}", package="bot_modules")
            except Exception:
                logger.exception(f'Error while importing module "{path.stem}"')


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
# download_data_delayed()
# data_downloaded()
#
# Command events:
# public!COMMAND(message:discord.Message, args:string)
# admin!COMMAND(message:discord.Message, args:string)
# owner!COMMAND(message:discord.Message, args:string)
