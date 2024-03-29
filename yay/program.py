from contextlib import contextmanager, suppress
from itertools import count
from types import MethodType

from ihex import IHex

from yay.cpu import make_cpu
from yay.helpers import inject_names, with_bind_program
from yay.mnemonic import Lit


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
        self.unique_name = None
        self.containing = None

    @property
    def was_called(self):
        return self.unique_name is not None

    def direct(self, *args, **kwargs):
        """
        TODO: Currently requires to explicitly pass the program instance
        when called.
        """
        return self.f(*args, **kwargs)

    def _add_names(self, names):
        self.f._add_names(names)
        self.emit_body = inject_names(names)(self.emit_body)

    def __call__(self, program):
        if not isinstance(program, Program):
            self.containing = program
            program = program.program
        if self.unique_name is None:
            self.unique_name = program.new_label_name(self.f.__name__)
        program.call(self.unique_name)

    def emit_body(self, program):
        if self.was_called:
            program.add_label(self.unique_name)
            self.f(program if self.containing is None else self.containing)
            program.ret()

    def __repr__(self):
        return (
            f"<sub object at {id(self):#x}, {self.f.__name__}, "
            f"was_called={self.was_called}, name={self.unique_name}>"
        )

    def clone(self):
        return type(self)(self.f)


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
        cls._mods = {
            mod.__name__: mod
            for mod in namespace.get("mods", [])
        }

    def mod(cls, module):
        cls._mods[module.__name__] = module
        return module


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

        for name, mod in self._mods.items():
            self._cpu_namespace[name] = mod.bind_program(self)

        if hasattr(self, "main"):
            self.main = inject_names(self._cpu_namespace)(self.main)

        self.subs = []

        macro_sources = [self.cpu["macros_from"]["macros_from"]]
        macro_sources.extend(type(self).__mro__)
        for cls in macro_sources:
            self._inject_macros(vars(cls))
            self.subs.extend(filter(is_sub, vars(cls).values()))

        self.labels = {}
        self.used_labels = set()
        self.position = 0
        self.offset = 0

        self._was_assembled = False

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
            f"is_{typename}"
        )(*args)

    def convert(self, mnemonic, from_, to, value):
        converted = getattr(
            self.cpu["parse_helpers"]["converters"],
            f"{to}_from_{from_}"
        )(mnemonic, value)
        if not self._matches_specific(to, converted, from_alternative=True):
            raise ValueError(
                f"Could not match {converted!r} (converted from {value!r}"
                f" ({from_!r})) as type {to!r}"
            )
        return converted

    def _assemble(self):
        if self._was_assembled:
            return

        self._was_assembled = True
        self.main()

        # Recursively make sure all subs that are part of mods and only
        # indirectly called (i. e. via another sub in a mod) are actually
        # called so that they are known by the program.
        # TODO: Refactor into either a better system or into own mathod.
        old_append = self.append
        self.append = lambda *args, **kwargs: None
        for sub in self.subs:
            if sub.was_called:
                sub.f(self if sub.containing is None else sub.containing)
        self.append = old_append

        for sub in self.subs:
            sub.emit_body(self)

    def _code_as_bytes(self):
        return b"".join(opcode.opcode for opcode in self._opcodes)

    def to_binary(self):
        self._assemble()
        return b"\0" * self.offset + self._code_as_bytes()

    def to_ihex(self, as_str=True):
        self._assemble()
        ihex = IHex()
        ihex.insert_data(self.offset, self._code_as_bytes())
        if as_str:
            return ihex.write()
        else:
            return ihex

    def get_position(self, searched):
        position = self.offset
        for mnemonic in self._opcodes:
            if mnemonic is searched:
                return position
            position += mnemonic.size
        raise ValueError(f"{searched} is not in this program.")

    def offsetof(self, label):
        return self.position - self.labels[label]

    def new_label_name(self, prefix):
        for n in count():
            name = f"{prefix}_{n}"
            if name not in self.used_labels:
                self.used_labels.add(name)
                return name

    def relocate(self, offset):
        if self.position != 0:
            raise RuntimeError(
                "Relocate must be called before program is assembled."
            )
        self.position = offset
        self.offset = offset

    @macro
    def add_binary_data(self, data):
        ptr = self.position
        for byte in data:
            Lit(byte)
        return ptr


@with_bind_program
class Mod:
    def __init__(self):
        for name in dir(self):
            value = getattr(self, name)
            if is_macro(value):
                with suppress(AttributeError):
                    value = value.clone()
                value._add_names(self.program._cpu_namespace)
                if is_sub(value):
                    self.program.subs.append(value)
                    value = MethodType(value, self)
                setattr(self, name, value)
