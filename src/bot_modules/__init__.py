import glob
import importlib
from os.path import dirname, basename, isfile

import logging
logger = logging.getLogger(__name__)


def import_modules():
    modules = glob.glob(dirname(__file__) + "/*.py")
    module_names = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
    for m in module_names:
        logger.info("Importing module \"{0}\"".format(m))

        # noinspection PyBroadException
        try:
            importlib.import_module("."+m, package="bot_modules")
        except Exception:
            logger.exception("Error while importing module \"{0}\"".format(m))
