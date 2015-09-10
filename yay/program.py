from contextlib import suppress

from yay.helpers import inject_names
from yay.cpu import make_cpu


class ProgramMeta(type):
    def __new__(cls, name, bases, namespace, **kwargs):
        return type.__new__(cls, name, bases, namespace)

    def __init__(self, name, bases, namespace, **kwargs):
        type.__init__(self, name, bases, namespace)
        with suppress(KeyError):
            self._cpu_spec = kwargs["cpu"]
        self._opcode_destination = kwargs.get("opcode_destination", list)


class Program(metaclass=ProgramMeta):
    def __init__(self):
        self._opcodes = self._opcode_destination()
        cpu = make_cpu(self._cpu_spec)
        self._cpu_namespace = {}
        for section_name in cpu["all"]:
            for name, item in cpu[section_name].items():
                try:
                    self._cpu_namespace[name] = item.bind_program(self)
                except AttributeError:
                    self._cpu_namespace[name] = item
        if hasattr(self, "main"):
            self.main = inject_names(self._cpu_namespace)(self.main)

    def append(self, mnemonic):
        self._opcodes.append(mnemonic)

    def to_binary(self):
        self.main()
        return b"".join(opcode.opcode for opcode in self._opcodes)
