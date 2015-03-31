class Accumulator:
    pass


class Register:
    def __init__(self, number, can_indirect=False):
        self.number = number
        self.can_indirect = can_indirect
        if can_indirect:
            self.as_indirect = IndirectRegister(number)
        else:
            self.as_indirect = None

    def __int__(self):
        return self.number

    def __str__(self):
        return "R{}".format(self.number)

    def __repr__(self):
        return "R{}()".format(self.number)


class IndirectRegister(Register):
    def __init__(self, number, can_indirect=True):
        super().__init__(number, False)
        self.can_indirect = True
        self.as_indirect = self
        self.indirect = True

    def __str__(self):
        return "IR{}".format(self.number)

    def __repr__(self):
        return "IR{}()".format(self.number)


class RegisterDefinitionMeta(type):
    @property
    def registers(self):
        registers = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                registers[key] = value
        registers.update(self._registers)
        return registers


class AT89S8253(metaclass=RegisterDefinitionMeta):
    A = Accumulator()

    R = [
        Register(0, True),
        Register(1, True),
        Register(2),
        Register(3),
        Register(4),
        Register(5),
        Register(6),
        Register(7)
    ]

    _registers = {}
    for _index, _register in enumerate(R):
        _registers["R{}".format(_index)] = _register

    # SFRs
    P1 = 0x90
