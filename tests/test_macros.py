from yay import Program as _Program, sub


class Program(_Program, cpu="AT89S8253"):
    pass


def test_xor():
    class XorTest(Program):
        def main(self):
            self.xor(ACC[2], ACC[4])

    class Expected(Program):
        def main(self):
            ldb(ACC[2])
            jnb(ACC[4], "dont_toggle")
            cpl(C)
            Label("dont_toggle")

    assert XorTest().to_binary() == Expected().to_binary()


def test_clear_port():
    bit_mask = 0x3A

    class ClearPortTest(Program):
        def main(self):
            self.clear_port(port=P1, bit_mask=bit_mask)

    class Expected(Program):
        def main(self):
            andl(P1, bit_mask)

    assert ClearPortTest().to_binary() == Expected().to_binary()


def test_set_port():
    bit_mask = 0x3A

    class SetPortTest(Program):
        def main(self):
            self.set_port(port=P1, bit_mask=bit_mask)

    class Expected(Program):
        def main(self):
            orl(P1, bit_mask)

    assert SetPortTest().to_binary() == Expected().to_binary()


def test_lsl():
    class LslTest(Program):
        def main(self):
            self.lsl()

    class Expected(Program):
        def main(self):
            clr(C)
            rlc()

    assert LslTest().to_binary() == Expected().to_binary()


def test_lsr():
    class LsrTest(Program):
        def main(self):
            self.lsr()

    class Expected(Program):
        def main(self):
            clr(C)
            rrc()

    assert LsrTest().to_binary() == Expected().to_binary()


def test_nested_loops():
    class NestedLoopTest(Program):
        def main(self):
            with self.loop(R0, 2), self.loop(R1, 4):
                nop()

    class Expected(Program):
        def main(self):
            mov(R0, 2)
            Label("loop_R0")
            mov(R1, 4)
            Label("loop_R1")
            nop()
            djnz(R1, "loop_R1")
            djnz(R0, "loop_R0")

    assert NestedLoopTest().to_binary() == Expected().to_binary()


def test_sub_direct():
    class Test(Program):
        def main(self):
            self.test_sub.direct(self)

        @sub
        def test_sub(self):
            nop()

    class Expected(Program):
        def main(self):
            nop()

    assert Test().to_binary() == Expected().to_binary()
