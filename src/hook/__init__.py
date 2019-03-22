import inspect


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
            cls.__registered_hooks[name] = cls()

        return cls.__registered_hooks[name]

    @classmethod
    def exists(cls, name):
        """
        Checks if a hook exists by the given name.
        :param name: Name of the hook to check.
        :return: True if the hook exists, False otherwise.
        """
        return name in cls.__registered_hooks

    def __init__(self):
        self.__methods = []

    def attach(self, method):
        """
        Attaches a method to this hook. The method will be executed after all previously added hooks. Both synchronous
        and asynchronous methods are supported.
        :param method: the method to attach to this hook.
        :return: True if the method was attached, False otherwise.
        """
        if method not in self.__methods:
            self.__methods.append(method)
            return True
        return False

    def detach(self, method):
        """
        Attaches the method from this hook, if it is attached.
        :param method: the method to detach from this hook.
        :return: True if the method was detached, False otherwise.
        """
        if method in self.__methods:
            self.__methods.remove(method)
            return True
        return False

    async def __call__(self, *args, **kwargs):
        """
        Calls the hook, executing the attached methods with the given arguments in the order they were added.
        :param args: Arguments to execute the attached methods with.
        :param kwargs: Keyword arguments to execute the attached methods with.
        :return: Nothing
        """
        for method in self.__methods:
            if inspect.iscoroutinefunction(method):
                await method(*args, **kwargs)
            else:
                method(*args, **kwargs)
