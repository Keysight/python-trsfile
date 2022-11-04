import functools


class alias:
    """
    A decorator for implementing method aliases.
    """

    def __init__(self, *aliases):
        self.aliases = set(aliases)

    def __call__(self, obj):
        if type(obj) == property:
            obj.fget._aliases = self.aliases
        else:
            obj._aliases = self.aliases

        return obj


def aliased(aliased_class):
    """
    A decorator for enabling method aliases.
    """
    def wrapper(func, name):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            return func(*args, **kwargs)
        return inner

    aliased_class_dict = aliased_class.__dict__.copy()
    aliased_class_set = set(aliased_class_dict)

    for name, method in aliased_class_dict.items():
        aliases = None

        if (type(method) == property) and hasattr(method.fget, '_aliases'):
            aliases = method.fget._aliases
        elif hasattr(method, '_aliases'):
            aliases = method._aliases

        if aliases:
            for method_alias in aliases - aliased_class_set:
                wrapped_method = wrapper(method, method_alias)
                wrapped_method.__doc__ = str(f"{method_alias} is an alias of {name}.")
                setattr(aliased_class, method_alias, wrapped_method)

    return aliased_class