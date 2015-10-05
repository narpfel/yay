from yay.helpers import InvalidRegisterError
from yay.program import macro, block_macro


class Macros:
    @block_macro
    def loop(self, register, n):
        MOV(register, n)
        Label("loop_head")
        yield
        DJNZ(register, "loop_head")


class Accumulator:
    def __add__(self, other):
        if isinstance(other, DPTR):
            return DptrOffset()
        elif isinstance(other, PC):
            return PcOffset()
        return NotImplemented


class DPTR:
    def __init__(self):
        self.can_indirect = True
        self.as_indirect = IndirectDptr()


class PC:
    pass


class DptrOffset:
    pass


class PcOffset:
    pass


class IndirectDptr:
    pass


class Carry:
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


class IndirectRegister:
    def __init__(self, number):
        self.indirect_number = number
        self.can_indirect = True
        self.as_indirect = self

    def __int__(self):
        return self.indirect_number

    def __str__(self):
        return "IR{}".format(self.indirect_number)

    def __repr__(self):
        return "IR{}()".format(self.indirect_number)


class Byte:
    def __init__(self, byte_addr):
        self.byte_addr = byte_addr

    def __int__(self):
        return self.byte_addr

    def __str__(self):
        return "Byte({})".format(self.byte_addr)


class SFR(Byte):
    def __init__(self, name, byte_addr):
        if byte_addr not in range(128, 257):
            raise ValueError(
                "`byte_addr` must be in range(128, 257), not {}"
                .format(byte_addr)
            )
        super().__init__(byte_addr)
        self.name = name
        self.bit_addressable = (
            self.byte_addr >= 0x80 and not self.byte_addr % 8
        )

    def __getitem__(self, bit):
        if not self.bit_addressable:
            raise TypeError("{} is not bit addressable".format(self))
        return Bit(self.byte_addr + bit)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "SFR(name={self.name!r}, byte_addr={self.byte_addr})".format(
            self=self
        )


class Bit:
    def __init__(self, bit_addr):
        self.bit_addr = bit_addr

    def __invert__(self):
        return NotBit(self.bit_addr)

    def __int__(self):
        return self.bit_addr

    def __repr__(self):
        return "Bit({})".format(self.bit_addr)


class NotBit:
    def __init__(self, not_bit_addr):
        self.not_bit_addr = not_bit_addr

    def __int__(self):
        return self.not_bit_addr

    def __repr__(self):
        return "~Bit({})".format(self.not_bit_addr)


class NamedBit(Bit):
    def __init__(self, name, bit_addr):
        super().__init__(bit_addr)
        self.name = name

    def __repr__(self):
        return "Bit(name={s.name!r}, bit_addr={s.bit_addr})".format(s=self)


def at(register):
    if isinstance(register, (DptrOffset, PcOffset)):
        return register

    try:
        if register.can_indirect:
            return register.as_indirect
        else:
            raise InvalidRegisterError(
                "{} can not be used as indirect.".format(register)
            )
    except AttributeError as err:
        raise TypeError("Not a register: {!r}.".format(register)) from err


class Label:
    def __init__(self, name):
        self.name = name
        self.program.add_label(name)

    @classmethod
    def bind_program(cls, program):
        return type(cls.__name__, (cls, ), dict(program=program))


# TODO: Circular import. `yay.cpus.MCS_51` needs a `matcher` attribute in order
# for `yay.cpu._import_object` to work correctly. Should `_import_object` be
# changed so that it can import modules from packages?
from yay.cpus.MCS_51 import matchers, converters
