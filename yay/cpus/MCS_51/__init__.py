from warnings import warn

from yay import macro, block_macro, sub, InvalidRegisterError, Mod
from yay.helpers import with_bind_program


class Macros:
    @block_macro
    def loop(self, register, n=None):
        if n is not None:
            mov(register, n)
        loop_head = self.new_label(f"loop_head_{register}")
        yield
        djnz(register, loop_head)

    @block_macro
    def until(self, operand, value):
        loop_head = self.new_label(f"until_{operand}_!=_{value}")
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
        label = self.new_label(f"wait_on_{bit}")
        jnb(bit, label)

    @block_macro
    def infinitely(self):
        loop = self.new_label("infinite_loop")
        yield
        if -127 < self.offsetof(loop) <= 128:
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
    def subt(self, subtrahend):
        """
        TODO: Name collision with `yay.sub`. For now, this is renamed to
        `subt`, but a better name should be found.
        """
        clr(C)
        subb(subtrahend)

    @sub
    def to_decimal(self):
        """Convert the value stored in `A` to a 3-digit decimal string and
        store it at `at(R0)`.

        Clobbers
        --------
            at(R0) .. at(R0 + 3): output
            A
        """
        with self.using(R1, R3):
            for _ in range(2):
                inc(R0)
            str(R1)
            with self.loop(R3, 2):
                mov(B, 10)
                div()
                str(R1)
                ldd(B)
                add(ord("0"))
                str(at(R0))
                dec(R0)
                ldr(R1)
            add(ord("0"))
            str(at(R0))


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
        stb(F0)
        self.program.subt(self.maximum - self.minimum)
        andl(~F0)
        stb(F0)
        add(self.maximum)
        ldb(F0)

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
    def write_byte(self, byte=None):
        self.program.wait_on(TI)
        if byte is None:
            std(SBUF)
        else:
            if isinstance(byte, (__builtins__["str"], bytes)) and len(byte) == 1:
                byte = ord(byte)
            mov(SBUF, byte)
        clr(TI)

    @sub
    def write_str(self):
        """
        Write string stored at `at(R0)` of length `R1`.

        Clobbers
        --------
            A
        """
        with self.program.using(R0, R1), self.program.loop(R1):
            ldr(at(R0))
            inc(R0)
            self.write_byte()

    @sub
    def write_byte_binary(self):
        """
        Write byte in `A` formatted as an unsigned binary number.

        Example
        -------
            A = 42 => 0b00101010

        Clobbers
        --------
            A
        """
        self.write_byte(ord("0"))
        self.write_byte(ord("b"))
        with self.program.using(R0, R1), self.program.loop(R0, 8):
            rl()
            str(R1)
            andl(1)
            add(ord("0"))
            self.write_byte()
            ldr(R1)


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


class OneWire(Mod):
    def __init__(self, pin):
        super().__init__()
        self.delay = self.program.delay
        self.pin = pin

    @macro
    def initialize(self):
        set(self.pin)

    @sub
    def reset(self):
        """
        Send reset pulse to the bus.

        Clobbers
        --------
            C: Indicates whether device is present on bus.
        """
        clr(self.pin)
        self.delay.us(500)
        set(self.pin)
        self.delay.us(65)
        ldb(self.pin)
        self.delay.us(500 - 65)

    @macro
    def write_byte(self, byte=None):
        """
        Write one byte to the bus.

        `byte` is sent if given, else `A` is sent.

        Clobbers
        --------
            A
        """
        if byte is not None:
            ldi(byte)
        self._write_byte()

    @sub
    def _write_byte(self):
        # Write byte in `A`
        with self.program.using(R0), self.program.loop(R0, 8):
            rrc()
            self.write_bit()

    @sub
    def read_byte(self):
        """
        Read one byte from the bus into `A`.

        Clobbers
        --------
            A
        """
        # Read byte into `A`
        swap()
        with self.program.using(R0), self.program.loop(R0, 8):
            self.read_bit()
            rrc()

    @sub
    def write_bit(self):
        """
        Write one bit from `C` to the bus.

        Clobbers
        --------
            R7: for microsecond delay
        """
        jnc("write_zero")

        clr(self.pin)
        self.delay.us(3)
        set(self.pin)
        self.delay.us(70)
        ret()

        Label("write_zero")
        clr(self.pin)
        self.delay.us(70)
        set(self.pin)

    @sub
    def read_bit(self):
        """
        Read one bit from the bus into `C`.

        Clobbers
        --------
            C: bit read from the bus
            R7: for microsecond delay
        """
        clr(self.pin)
        self.delay.us(3)
        set(self.pin)
        self.delay.us(8)
        ldb(self.pin)
        self.delay.us(50)


class Ds18b20(OneWire):
    COMMANDS = {
        "search_rom": 0xf0,
        "read_rom": 0x33,
        "_match_rom": 0x55,
        "skip_rom": 0xcc,
        "alarm_search": 0xec,
        "convert_t": 0x44,
        "write_scratchpad": 0x4e,
        "_read_scratchpad": 0xbe,
        "copy_scratchpad": 0x48,
        "recall_e2": 0xb8,
        "read_power_supply": 0xb4,
    }

    def __init__(self, pin, single_drop):
        super().__init__(pin)
        self.single_drop = single_drop

    def __getattr__(self, name):
        if name in self.COMMANDS:
            return lambda: self.write_byte(self.COMMANDS[name])
        else:
            raise AttributeError(f"`{self}` has not attribute `{name}`")

    @sub
    def match_rom(self):
        """Match ROM using the address stored at `at(DPTR)`. Destroys `DPTR`.

        Raises a `UserWarning` and issues a `skip_rom` command if in
        single-drop mode.

        Clobbers
        --------
            DPTR
        """

        if self.single_drop:
            warn(
                "Match ROM not necessary in single-drop mode, using `skip_rom`."
            )
            self.skip_rom()
        else:
            self._match_rom()
            with self.program.using(R1), self.program.loop(R1, 8):
                ldx(at(DPTR))
                inc(DPTR)
                self.write_byte()

    @sub
    def read_temperature(self):
        """Read temperature from sensor with address stored at `at(DPTR)`.

        Clobbers
        --------
            DPTR
            R1
        """
        self.reset()
        self.match_rom()
        self.read_scratchpad(2)

    @macro
    def read_scratchpad(self, bytes):
        """Read scratchpad into `at(R0)`.

        Clobbers
        --------
            at(R0) .. at(R0 + bytes): scratchpad contents
            R1
        """
        if bytes not in range(1, 10):
            raise ValueError(f"`bytes` must be in range(1, 10), not `{bytes}`.")

        mov(R1, bytes)
        self._read_scratchpad_for_R1_bytes()

    @sub
    def _read_scratchpad_for_R1_bytes(self):
        self._read_scratchpad()
        with self.program.loop(R1):
            self.read_byte()
            str(at(R0))
            inc(R0)


# TODO: Circular import. `yay.cpus.MCS_51` needs a `matcher` attribute in order
# for `yay.cpu._import_object` to work correctly. Should `_import_object` be
# changed so that it can import modules from packages?
from yay.cpus.MCS_51 import matchers, converters
