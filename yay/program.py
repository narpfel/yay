from contextlib import suppress, contextmanager
from functools import partial
from types import MethodType

from yay.helpers import inject_names
from yay.cpu import make_cpu


def macro(f):
    # Make sure each macro has its own `__globals__` dict so `add_names` can
    # `update` it without affecting other global namespaces.
    f = inject_names({})(f)
    def add_names(names):
        f.__globals__.update(names)
    f._add_names = add_names
    f.is_macro = True
    return f


def block_macro(f):
    f = macro(f)
    context_f = contextmanager(f)
    context_f._add_names = f._add_names
    context_f.is_macro = f.is_macro
    return context_f


def is_macro(f):
    return getattr(f, "is_macro", False)


class ProgramMeta(type):
    def __new__(cls, name, bases, namespace, **kwargs):
        return type.__new__(cls, name, bases, namespace)

    def __init__(self, name, bases, namespace, **kwargs):
        type.__init__(self, name, bases, namespace)
        with suppress(KeyError):
            self._cpu_name = kwargs["cpu"]
        self._opcode_destination = kwargs.get("opcode_destination", list)


class Program(metaclass=ProgramMeta):
    def __init__(self):
        self._opcodes = self._opcode_destination()
        self.cpu = make_cpu(self._cpu_name)
        self._cpu_namespace = {}
        for section_name in self.cpu["all"]:
            for name, item in self.cpu[section_name].items():
                try:
                    self._cpu_namespace[name] = item.bind_program(self)
                except AttributeError:
                    self._cpu_namespace[name] = item
        if hasattr(self, "main"):
            self.main = inject_names(self._cpu_namespace)(self.main)

        self._inject_macros(vars(self.cpu["macros_from"]["macros_from"]))
        self._inject_macros(vars(type(self)))

        self.labels = {}
        self.position = 0

    def _inject_macros(self, macros):
        for name, value in macros.items():
            if is_macro(value):
                value._add_names(self._cpu_namespace)
                setattr(self, name, MethodType(value, self))

    def append(self, mnemonic):
        self._opcodes.append(mnemonic)
        self.position += mnemonic.size

    def add_label(self, label):
        self.labels[label] = self.position

    def matches(self, typename, value):
        possible_matchers = [typename]
        possible_matchers.extend(
            self.cpu["signature_contents"][typename].get("alternatives", [])
        )
        for matcher_type in possible_matchers:
            if self._matches_specific(matcher_type, value):
                return True, matcher_type
        return False, ""

    def _matches_specific(self, typename, value, from_alternative=None):
        args = [value]
        if from_alternative is not None:
            args.append(from_alternative)
        return getattr(
            self.cpu["parse_helpers"]["matchers"],
            "is_{}".format(typename)
        )(*args)

    def convert(self, mnemonic, from_, to, value):
        converted = getattr(
            self.cpu["parse_helpers"]["converters"],
            "{}_from_{}".format(to, from_)
        )(mnemonic, value)
        if not self._matches_specific(to, converted, from_alternative=True):
            raise ValueError(
                "Could not match {!r} (converted from {!r} ({!r})) as type {!r}"
                .format(
                    converted, value, from_, to
                )
            )
        return converted

    def to_binary(self):
        self.main()
        return b"".join(opcode.opcode for opcode in self._opcodes)

    def get_position(self, mnemonic):
        return self._opcodes.index(mnemonic)
