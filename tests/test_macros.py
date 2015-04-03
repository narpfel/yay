from pytest import importorskip

importorskip("yay.macros")
from yay.macros import xor, clear_port, set_port, lsl, lsr

# TODO: quick and dirty
from yay.registers import AT89S8253
globals().update(AT89S8253.registers)

from yay.program import Program as _Program


class Program(_Program, cpu="AT89S8253"):
    pass


def test_xor():
    left, right = A[2], A[4]

    class XorTest(Program):
        def main(self):
            xor(left, right)

    class Expected(Program):
        def main(self):
            LDB(left)
            JNB(right, "dont_toggle")
            CPL(C)
            LABEL("dont_toggle")

    assert XorTest().to_binary() == Expected().to_binary()


def test_clear_port():
    bit_mask = 0x3A
    port = P1

    class ClearPortTest(Program):
        def main(self):
            clear_port(port=port, bit_mask=bit_mask)

    class Expected(Program):
        def main(self):
            AND(port, bit_mask)

    assert ClearPortTest().to_binary() == Expected().to_binary()


def test_set_port():
    bit_mask = 0x3A
    port = P1

    class SetPortTest(Program):
        def main(self):
            set_port(port=port, bit_mask=bit_mask)

    class Expected(Program):
        def main(self):
            OR(port, bit_mask)

    assert SetPortTest().to_binary() == Expected().to_binary()


def test_lsl():
    class LslTest(Program):
        def main(self):
            lsl()

    class Expected(Program):
        def main(self):
            CLR(C)
            RLC()

    assert LslTest().to_binary() == Expected().to_binary()


def test_lsr():
    class LsrTest(Program):
        def main(self):
            lsr()

    class Expected(Program):
        def main(self):
            CLR(C)
            RRC()

    assert LsrTest().to_binary() == Expected().to_binary()
