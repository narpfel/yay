from warnings import warn

from yay import macro, block_macro, sub, InvalidRegisterError, Mod
from yay.helpers import with_bind_program


class Accumulator:
    def __init__(self):
        self.direct_address = 0xe0

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
        self.program = None
        self.number = number
        self.can_indirect = can_indirect
        if can_indirect:
            self.as_indirect = IndirectRegister(number)
        else:
            self.as_indirect = None

    def __int__(self):
        return self.number

    def __str__(self):
        return f"R{self.number}"

    def __repr__(self):
        return f"R{self.number}()"

    @property
    def direct_address(self):
        # TODO: Respect currently selected register bank
        # return self.number + self.program.bank * 8
        return self.number

    def bind_program(self, program):
        if self.program is not None:
            raise RuntimeError("`Register.bind_program` called multiply")
        self.program = program
        return self


class IndirectRegister:
    def __init__(self, number):
        self.indirect_number = number
        self.can_indirect = True
        self.as_indirect = self

    def __int__(self):
        return self.indirect_number

    def __str__(self):
        return f"IR{self.indirect_number}"

    def __repr__(self):
        return f"IR{self.indirect_number}()"


class Byte:
    def __init__(self, byte_addr):
        self.byte_addr = byte_addr

    def __int__(self):
        return self.byte_addr

    def __str__(self):
        return f"Byte({self.byte_addr})"


class SFR(Byte):
    def __init__(self, name, byte_addr):
        if byte_addr not in range(128, 256):
            raise ValueError(
                f"`byte_addr` must be in range(128, 256), not {byte_addr}"
            )
        super().__init__(byte_addr)
        self.name = name
        self.bit_addressable = (
            self.byte_addr >= 0x80 and not self.byte_addr % 8
        )

    def __getitem__(self, bit):
        if not self.bit_addressable:
            raise TypeError(f"{self} is not bit addressable")
        return Bit(self.byte_addr + bit)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"SFR(name={self.name!r}, byte_addr={self.byte_addr})"


class Bit:
    def __init__(self, bit_addr):
        self.bit_addr = bit_addr

    def __invert__(self):
        return NotBit(self.bit_addr)

    def __int__(self):
        return self.bit_addr

    def __repr__(self):
        return f"Bit({self.bit_addr})"


class NotBit:
    def __init__(self, not_bit_addr):
        self.not_bit_addr = not_bit_addr

    def __int__(self):
        return self.not_bit_addr

    def __repr__(self):
        return f"~Bit({self.not_bit_addr})"


class NamedBit(Bit):
    def __init__(self, name, bit_addr):
        super().__init__(bit_addr)
        self.name = name

    def __repr__(self):
        return f"Bit(name={self.name!r}, bit_addr={self.bit_addr})"


def at(register):
    if isinstance(register, (DptrOffset, PcOffset)):
        return register

    try:
        if register.can_indirect:
            return register.as_indirect
        else:
            raise InvalidRegisterError(f"{register} can not be used as indirect.")
    except AttributeError as err:
        raise TypeError(f"Not a register: {register!r}.") from err


@with_bind_program
class Label:
    def __init__(self, name):
        self.name = name
        self.program.add_label(name)


class LookupTableDptr(Mod):
    def __init__(self, value_map, itemlength):
        super().__init__()
        self.itemlength = itemlength
        items = sorted(value_map.items())
        self.minimum = items[0][0]
        self.maximum = items[-1][0]
        table = bytearray(itemlength * (self.maximum - self.minimum + 1))

        for (key, value) in items:
            key -= self.minimum
            length = len(value)
            if length < itemlength:
                value += b"\0" * (itemlength - length)
            table[key * itemlength:key * (itemlength + 1)] = value

        self.position = self.program.add_binary_data(table)

    @sub
    def lookup(self):
        """
        Lookup `A`, returning the value in `A`.

        Iff `self` does not contain `A`, `C` is set and the contents of `A`
        are not changed.
        """
        not_in_range = self.new_label_name("not_in_range")

        self.in_range.direct()
        jnc(not_in_range)

        self.lookup_unsafe.direct()
        ret()

        Label(not_in_range)
        set(C)

    @sub
    def in_range(self):
        """Check if `A` is in range of this LUT, i. e. is a possible value."""
        self.program.subt(self.minimum)
        mov(F0, C)
        self.program.subt(self.maximum - self.minimum)
        andl(~F0)
        mov(F0, C)
        add(self.maximum)
        mov(C, F0)

    @sub
    def lookup_unsafe(self):
        self.program.subt(self.minimum)
        if self.itemlength == 1:
            pass
        elif self.itemlength == 2:
            self.lsr()
        else:
            mov(B, self.itemlength)
            mul()
        mov(B, A)
        if self.itemlength != 1:
            inc(B)
        mov(DPTR, self.position)
        lpm(at(A + DPTR))


class Delay(Mod):
    def __init__(self):
        super().__init__()
        # TODO: Currently does not account for x2 mode.
        self.cycles_per_ms = self.program.F_CPU / 12 / 1000
        self.cycles_per_us = self.cycles_per_ms / 1000
        self.inner_loop_count = 22
        inner_loop_cycles = 4
        inner_loop_total = inner_loop_cycles * self.inner_loop_count
        self.outer_loop_count = int(self.cycles_per_ms / (inner_loop_total + 4))
        elapsed_per_ms = (inner_loop_total + 4) * self.outer_loop_count
        self.delta = int(self.cycles_per_ms - elapsed_per_ms + 0.5)

    @macro
    def us(self, time):
        """
        Busy wait for `time` microseconds.

        Clobbers
        --------
            R7
        """
        cycles = int(time * self.cycles_per_us + 0.5 - 2)
        iterations, remaining_cycles = divmod(cycles, 4)
        if iterations > 255:
            max_cycles = 255 * 4 + 2
            raise ValueError(
                f"Cannot wait for {cycles} cycles, maximum is "
                f"{max_cycles} cycles ({max_cycles / self.cycles_per_us}"
                " us), use `ms` instead"
            )
        mov(R7, iterations)
        if iterations > 0:
            with self.program.loop(R7):
                nop()
        for _ in range(remaining_cycles):
            nop()

    @macro
    def ms(self, time):
        """Wait for `time` milliseconds.

        Clobbers
        --------
            A
        """
        if time > 0:
            mov(A, time)
            self._delay_ms()

    @sub
    def _delay_ms(self):
        """Busy wait for `A` ms."""
        with self.program.using(R0, R1, R2):
            mov(R0, A)
            with self.program.loop(R0):
                self._delay_one_ms()

    @macro
    def _delay_one_ms(self):
        with self.program.loop(R1, self.outer_loop_count):
            with self.program.loop(R2, self.inner_loop_count):
                nop()
                nop()
        if self.delta >= 5:
            with self.program.loop(R1, (self.delta - 2) // 3):
                nop()
        else:
            for _ in range(self.delta):
                nop()
