import ast
import sys
from collections.abc import Mapping
from copy import deepcopy
from functools import lru_cache, wraps
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from types import FunctionType, MethodType

from pkg_resources import resource_filename

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

import yay_ast


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
        raise ValueError(f"`number` not in `{allowed_values}`")
    return number & (2 ** bits - 1)


def inject_names(names):
    def decorator(f):
        f_globals = dict(getattr(f, "_initial_globals", f.__globals__))
        f_globals.update(names)

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


class MovTransformer(yay_ast.NodeTransformer):
    def visit_ArrowAssign(self, node):
        if len(node.targets) > 1:
            raise RuntimeError("This cannot happen!")

        mov_expr = yay_ast.copy_location(
            yay_ast.Expr(
                yay_ast.Call(
                    func=yay_ast.Name(id="mov", ctx=yay_ast.Load()),
                    args=[node.targets[0], node.value],
                    keywords=[]
                )
            ),
            node
        )
        return mov_expr


class ToPythonAstTransformer(yay_ast.NodeTransformer):
    def replace_node(self, node):
        self.generic_visit(node)

        PyAstType = getattr(ast, type(node).__name__)
        return ast.copy_location(
            PyAstType(**dict(yay_ast.iter_fields(node))),
            node
        )

    def __getattr__(self, name):
        if not name.startswith("visit_"):
            raise AttributeError
        return self.replace_node


class YayFileLoader(SourceFileLoader):
    def source_to_code(self, data, *args, **kwargs):
        node = yay_ast.parse(data)
        node = MovTransformer().visit(node)
        node = ToPythonAstTransformer().visit(node)
        ast.fix_missing_locations(node)
        return super().source_to_code(
            node,
            *args,
            **kwargs
        )


def import_yay_file(yay_filename, name="main"):
    spec = spec_for_yay_file(yay_filename, name)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def spec_for_yay_file(yay_filename, module_name="main"):
    loader = YayFileLoader(module_name, yay_filename)
    return spec_from_loader(loader.name, loader)


class YayFinder:
    def find_on_path(self, name):
        parts = name.split(".")
        for path in map(Path, sys.path):
            filename = path.joinpath(*parts).with_suffix(".yay")
            if filename.exists():
                return str(filename)

    def find_spec(self, name, path, target=None):
        if target is not None:
            raise ImportError("`target is not None` case is not supported")

        filename = self.find_on_path(name)
        if filename is not None:
            return spec_for_yay_file(filename, name)
