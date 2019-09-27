import inspect
import logging
import asyncio

logger = logging.getLogger(__name__)


class Hook:
    """
    Represents a set of methods which are to be called at a certain time. Typically, this is during some external event
    for which a single override can be made. A hook allows many modules to attach to this callback and run their own
    methods.
    """
    __registered_hooks = {}

    @classmethod
    def get(cls, name) -> "Hook":
        """
        Gets the hook for a given name, creating it if it does not exist. Not required, but useful for sharing hooks.
        :param name: Name of the hook to retrieve.
        :return: The hook for the given name.
        """
        if not Hook.exists(name):
            cls.__registered_hooks[name] = cls(name)

        return cls.__registered_hooks[name]

    @classmethod
    def list(cls):
        """
        Gets a list of registered hook names.
        :return: List of registered hook names
        """
        return sorted(cls.__registered_hooks.keys())

    @classmethod
    def exists(cls, name):
        """
        Checks if a hook exists by the given name.
        :param name: Name of the hook to check.
        :return: True if the hook exists, False otherwise.
        """
        return name in cls.__registered_hooks

    def __init__(self, name=None):
        self.__methods = []
        self.__name = name

    def attach(self, method):
        """
        Attaches a method to this hook. The method will be executed after all previously added hooks. Both synchronous
        and asynchronous methods are supported.
        :param method: the method to attach to this hook.
        :return: True if the method was attached, False otherwise.
        """
        if self.__name is not None:
            hook_desc = f'"{self.__name}"'
        else:
            hook_desc = f"with id {id(self)}"

        if hasattr(method, "__module__"):
            method_desc = f"{method.__module__}.{method.__qualname__}"
        else:
            method_desc = method.__qualname__

        if method not in self.__methods:
            self.__methods.append(method)
            logger.info(f"Attached method {method_desc} to hook {hook_desc}")
            return True
        else:
            logger.warning(f"Method {method_desc} already attached to hook {hook_desc}")
            return False

    def detach(self, method):
        """
        Attaches the method from this hook, if it is attached.
        :param method: the method to detach from this hook.
        :return: True if the method was detached, False otherwise.
        """

        if self.__name is not None:
            hook_desc = f'"{self.__name}"'
        else:
            hook_desc = f"with id {id(self)}"

        if hasattr(method, "__module__"):
            method_desc = f"{method.__module__}.{method.__qualname__}"
        else:
            method_desc = method.__qualname__

        if method in self.__methods:
            self.__methods.remove(method)
            logger.info(f"Detached method {method_desc} from hook {hook_desc}")
            return True
        else:
            logger.warning(f"Method {method_desc} not attached to hook {hook_desc}")
        return False

    def methods(self):
        """
        Returns a list of the methods attached to this hook.
        :return: List of methods attached to the hook
        """
        return self.__methods.copy()

    async def __call__(self, *args, **kwargs):
        """
        Calls the hook, executing the attached methods. Coroutines are scheduled to run concurrently.
        :param args: Arguments to execute the attached methods with.
        :param kwargs: Keyword arguments to execute the attached methods with.
        """
        tasks = []
        for method in self.__methods:
            try:
                if inspect.iscoroutinefunction(method):
                    tasks.append(asyncio.ensure_future(method(*args, **kwargs)))
                else:
                    method(*args, **kwargs)
            except Exception as e:
                if self.__name is not None:
                    logger.exception(f"Exception in hook {self.__name} from module {method.__module__}:")
                else:
                    raise e

        for task in tasks:
            try:
                await task
            except Exception as e:
                if self.__name is not None:
                    logger.exception(f"Exception in hook {self.__name} from async method:")
                else:
                    raise e
