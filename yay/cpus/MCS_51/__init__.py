from yay import macro, block_macro, sub, InvalidRegisterError, Mod
from yay.helpers import with_bind_program


class Macros:
    @block_macro
    def loop(self, register, n=None):
        if n is not None:
            mov(register, n)
        loop_head = self.new_label("loop_head_{}".format(register))
        yield
        djnz(register, loop_head)

    @block_macro
    def until(self, operand, value):
        loop_head = self.new_label("until_{}_!=_{}".format(operand, value))
        yield
        cjne(operand, value, loop_head)

    @block_macro
    def ifeq(self, operand, value):
        not_equal = self.new_label_name("not_equal")
        cjne(operand, value, not_equal)
        yield
        Label(not_equal)

    @block_macro
    def skip(self):
        down = self.new_label_name("down")
        ljmp(down)
        yield
        Label(down)

    @block_macro
    def using(self, *registers):
        for reg in registers:
            push(reg)
        yield
        for reg in reversed(registers):
            pop(reg)

    @macro
    def new_label(self, prefix="label"):
        name = self.new_label_name(prefix)
        Label(name)
        return name

    @macro
    def wait_on(self, bit):
        label = self.new_label("wait_on_{}".format(bit))
        jnb(bit, label)

    @block_macro
    def infinitely(self):
        loop = self.new_label("infinite_loop")
        yield
        if self.offsetof(loop) >= -126:
            sjmp(loop)
        else:
            ljmp(loop)

    @macro
    def call(self, label):
        lcall(label)

    @macro
    def ret(self):
        ret()

    @macro
    def clear_port(self, port, bit_mask):
        andl(port, bit_mask)

    @macro
    def set_port(self, port, bit_mask):
        orl(port, bit_mask)

    @macro
    def xor(self, left, right):
        ldb(left)
        label = self.new_label_name("skip_toggle")
        jnb(right, label)
        cpl(C)
        Label(label)

    @macro
    def lsl(self):
        clr(C)
        rlc()

    @macro
    def lsr(self):
        clr(C)
        rrc()

    @macro
    def sub(self, subtrahend):
        clr(C)
        subb(subtrahend)


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
        return "R{}".format(self.number)

    def __repr__(self):
        return "R{}()".format(self.number)

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
        if byte_addr not in range(128, 256):
            raise ValueError(
                "`byte_addr` must be in range(128, 256), not {}"
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
        self.program.sub(self.minimum)
        stb(F0)
        self.program.sub(self.maximum - self.minimum)
        andl(~F0)
        stb(F0)
        add(self.maximum)
        ldb(F0)

    @sub
    def lookup_unsafe(self):
        self.program.sub(self.minimum)
        if self.itemlength == 1:
            pass
        elif self.itemlength == 2:
            self.lsr()
        else:
            mov(B, self.itemlength)
            mul()
        std(B)
        if self.itemlength != 1:
            inc(B)
        mov(DPTR, self.position)
        lpm(at(A + DPTR))


class BlockingUart(Mod):
    """
    TODO: Generalize. Currently, `setup` assumes `F_CPU = 22118400` and
    a baudrate of 9600.
    """
    @macro
    def setup(self):
        mov(TH1, 244)
        ldd(TMOD)
        andl(0x0F)
        add(0x20)
        std(TMOD)
        clr(SM0)
        set(SM1)
        set(TR1)
        ldd(PCON)
        orl(0x80)
        std(PCON)
        set(REN)
        set(TI)
        clr(RI)

    @macro
    def read_byte(self):
        self.program.wait_on(RI)
        ldd(SBUF)
        clr(RI)

    @macro
    def write_byte(self):
        self.program.wait_on(TI)
        std(SBUF)
        clr(TI)


class Delay(Mod):
    def __init__(self):
        super().__init__()
        # TODO: Currently does not account for x2 mode.
        self.cycles_per_ms = self.program.F_CPU / 12 / 1000
        self.inner_loop_count = 22
        inner_loop_cycles = 4
        inner_loop_total = inner_loop_cycles * self.inner_loop_count
        self.outer_loop_count = int(self.cycles_per_ms / (inner_loop_total + 4))
        elapsed_per_ms = (inner_loop_total + 4) * self.outer_loop_count
        self.delta = int(self.cycles_per_ms - elapsed_per_ms + 0.5)

    @macro
    def ms(self, time):
        if time > 0:
            ldi(time)
            self._delay_ms()

    @sub
    def _delay_ms(self):
        """Busy wait for `A` ms."""
        with self.program.using(R0, R1, R2):
            str(R0)
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


# TODO: Circular import. `yay.cpus.MCS_51` needs a `matcher` attribute in order
# for `yay.cpu._import_object` to work correctly. Should `_import_object` be
# changed so that it can import modules from packages?
from yay.cpus.MCS_51 import matchers, converters
