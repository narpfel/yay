from contextlib import suppress, contextmanager
from itertools import count
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


class sub:
    def __init__(self, f):
        self.f = macro(f)
        self.is_macro = True
        self.is_sub = True
        self.was_called = False

    def _add_names(self, names):
        self.f._add_names(names)
        self.emit_body = inject_names(names)(self.emit_body)

    def __call__(self, program):
        self.was_called = True
        program.call(self.f.__name__)

    def emit_body(self, program):
        if self.was_called:
            Label(self.f.__name__)
            self.f(program)
            ret()


def is_macro(f):
    return getattr(f, "is_macro", False)


def is_sub(candidate):
    return getattr(candidate, "is_sub", False)


class ProgramMeta(type):
    def __new__(metacls, name, bases, namespace, **kwargs):
        return type.__new__(metacls, name, bases, namespace)

    def __init__(cls, name, bases, namespace, **kwargs):
        type.__init__(cls, name, bases, namespace)
        with suppress(KeyError):
            cls._cpu_name = kwargs["cpu"]
        cls._opcode_destination = kwargs.get("opcode_destination", list)


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

        self.subs = []

        macro_sources = [self.cpu["macros_from"]["macros_from"]]
        macro_sources.extend(type(self).__mro__)
        for cls in macro_sources:
            self._inject_macros(vars(cls))
            self.subs.extend(filter(is_sub, vars(cls).values()))

        self.labels = {}
        self.position = 0
        self.offset = 0

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
        for sub in self.subs:
            sub.emit_body(self)
        return b"\0" * self.offset + b"".join(opcode.opcode for opcode in self._opcodes)

    def get_position(self, searched):
        position = self.offset
        for mnemonic in self._opcodes:
            if mnemonic is searched:
                return position
            position += mnemonic.size
        raise ValueError("{} is not in this program.".format(searched))

    def offsetof(self, label):
        return self.position - self.labels[label]

    def new_label_name(self, prefix):
        for n in count():
            name = "{}_{}".format(prefix, n)
            if name not in self.labels:
                return name

    def relocate(self, offset):
        self.position = offset
        self.offset = offset
