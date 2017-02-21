from functools import wraps, lru_cache
from copy import deepcopy
from importlib.machinery import SourceFileLoader
from types import FunctionType, MethodType
from collections.abc import Mapping
from pkg_resources import resource_filename

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


class InvalidRegisterError(ValueError):
    pass


class InvalidConfigError(ValueError):
    pass


class WrongSignatureException(TypeError):
    pass


def config_filename(config_name):
    return resource_filename("yay", config_name)


@lru_cache()
def _read_config_cached(config_name):
    with open(config_name) as yaml_file:
        return load(yaml_file, Loader=Loader)


def read_config(config_name):
    return deepcopy(_read_config_cached(config_name))


def reverse_dict(mapping):
    if len(set(mapping)) != len(set(mapping.values())):
        raise ValueError("Mapping values not unique.")
    return {value: key for key, value in mapping.items()}


def recursive_merge(base, update):
    if not isinstance(base, Mapping) or not isinstance(update, Mapping):
        return update

    merged = dict(base)
    merged.update(update)
    for key in base.keys() & update.keys():
        merged[key] = recursive_merge(base[key], update[key])
    return merged


def twos_complement(number, bits, ranged=True):
    """Normalize negative values to their two’s complement values.

    Positive values are left unchanged if they are in ``range(2**bits)``,
    otherwise the last `bits` bits of them are taken.
    """
    allowed_values = range(-2**(bits - 1), 2**bits)
    if ranged and number not in allowed_values:
        raise ValueError("`number` not in `{}`".format(allowed_values))
    return number & (2 ** bits - 1)


def inject_names(names):
    def decorator(f):
        f_globals = dict(names)
        f_globals.update(getattr(f, "_initial_globals", f.__globals__))

        new_f = FunctionType(
            f.__code__,
            f_globals,
            argdefs=f.__defaults__,
            closure=f.__closure__
        )
        new_f._initial_globals = f.__globals__
        new_f = wraps(f)(new_f)

        if hasattr(f, "__self__"):
            new_f = MethodType(new_f, f.__self__)

        return new_f
    return decorator


def _bind_program(cls, program):
    return type(cls.__name__, (cls, ), dict(program=program))


def with_bind_program(cls):
    cls.bind_program = classmethod(_bind_program)
    return cls


def ignore_self(function):
    @wraps(function)
    def decorated(*args, **kwargs):
        return function(*args, **kwargs)
    return decorated


def import_yay_file(yay_filename):
    return SourceFileLoader("main", yay_filename).load_module()
