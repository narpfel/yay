from contextlib import suppress

import yay.cpu
from yay.helpers import inject_names


class ProgramMeta(type):
    def __new__(cls, name, bases, namespace, **kwargs):
        return type.__new__(cls, name, bases, namespace)

    def __init__(self, name, bases, namespace, **kwargs):
        type.__init__(self, name, bases, namespace)
        with suppress(KeyError):
            self._cpu = kwargs["cpu"]
        self._opcode_destination = kwargs.get("opcode_destination", list)


# TODO: dirty, remove leading underscore and make “real” CPU specific classes.
class _Program(metaclass=ProgramMeta):
    def __init__(self):
        self._opcodes = self._opcode_destination()
        self._cpu_namespace = {}
        for name, item in self._cpu.all.items():
            try:
                self._cpu_namespace[name] = item.bind_target(self._opcodes)
            except AttributeError:
                self._cpu_namespace[name] = item
        if hasattr(self, "main"):
            self.main = inject_names(self._cpu_namespace)(self.main)


    def to_binary(self):
        self.main()
        return b"".join(opcode.opcode for opcode in self._opcodes)


class Program(_Program, cpu=yay.cpu.AT89S8253):
    pass
