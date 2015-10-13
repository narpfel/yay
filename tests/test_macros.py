from yay.program import Program as _Program


class Program(_Program, cpu="AT89S8253"):
    pass


def test_xor():
    class XorTest(Program):
        def main(self):
            self.xor(ACC[2], ACC[4])

    class Expected(Program):
        def main(self):
            LDB(ACC[2])
            JNB(ACC[4], "dont_toggle")
            CPL(C)
            Label("dont_toggle")

    assert XorTest().to_binary() == Expected().to_binary()


def test_clear_port():
    bit_mask = 0x3A

    class ClearPortTest(Program):
        def main(self):
            self.clear_port(port=P1, bit_mask=bit_mask)

    class Expected(Program):
        def main(self):
            AND(P1, bit_mask)

    assert ClearPortTest().to_binary() == Expected().to_binary()


def test_set_port():
    bit_mask = 0x3A

    class SetPortTest(Program):
        def main(self):
            self.set_port(port=P1, bit_mask=bit_mask)

    class Expected(Program):
        def main(self):
            OR(P1, bit_mask)

    assert SetPortTest().to_binary() == Expected().to_binary()


def test_lsl():
    class LslTest(Program):
        def main(self):
            self.lsl()

    class Expected(Program):
        def main(self):
            CLR(C)
            RLC()

    assert LslTest().to_binary() == Expected().to_binary()


def test_lsr():
    class LsrTest(Program):
        def main(self):
            self.lsr()

    class Expected(Program):
        def main(self):
            CLR(C)
            RRC()

    assert LsrTest().to_binary() == Expected().to_binary()
