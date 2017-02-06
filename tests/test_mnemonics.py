from pytest import raises, mark

from yay.program import Program as _Program
from yay.helpers import InvalidRegisterError, WrongSignatureException


class Program(_Program, cpu="AT89S8253"):
    pass


def test_insert_in_opcodes():
    add_, and_ = None, None
    class Test(Program):
        def main(self):
            nonlocal add_, and_
            add_ = add(R3)
            and_ = andl(42)
    test = Test()
    binary = test.to_binary()
    assert add_ is not None
    assert and_ is not None
    assert test._opcodes == [add_, and_]
    assert binary == b"".join([add_.opcode, and_.opcode])


def test_ACALL():
    class Test(Program):
        def main(self):
            acall_ = acall(1234)
    assert Test().to_binary() == bytes([0b10010001, 0b11010010])


def test_ADD():
    class Test(Program):
        def main(self):
            add(R3)
            add(Byte(42))
    assert Test().to_binary() == bytes([0b00101011, 0b00100101, 42])


    class Test(Program):
        def main(self):
            add(R3, A)
    with raises(WrongSignatureException):
        Test().to_binary()

    class Test(Program):
        def main(self):
            add(42, A)
    with raises(WrongSignatureException):
        Test().to_binary()


def test_ADD_at():
    class Test(Program):
        def main(self):
            add(at(R1))
    assert Test().to_binary() == bytes([0b00100111])

    class Test(Program):
        def main(self):
            add(at(R4))
    with raises(InvalidRegisterError):
        Test().to_binary()

    class Test(Program):
        def main(self):
            add(at(1))
    with raises(TypeError):
        Test().to_binary()

    class Test(Program):
        def main(self):
            add(at(R1), A)
    with raises(TypeError):
        Test().to_binary()

    class Test(Program):
        def main(self):
            add(at(42), A)
    with raises(TypeError):
        Test().to_binary()


def test_ADD_immediate():
    class Test(Program):
        def main(self):
            add(42)
    assert Test().to_binary() == bytes([0b00100100, 42])

    class Test(Program):
        def main(self):
            add(420)
    with raises(WrongSignatureException):
        Test().to_binary()

    class Test(Program):
        def main(self):
            add(42, A)
    with raises(TypeError):
        Test().to_binary()

    class Test(Program):
        def main(self):
            add(R1, A)
    with raises(TypeError):
        Test().to_binary()


def test_ADDC():
    class Test(Program):
        def main(self):
            addc(R7)
            addc(Byte(127))

    assert Test().to_binary() == bytes(
        [0b00111111, 0b00110101, 127]
    )

    class Test(Program):
        def main(self):
            addc(-127)
            addc(250)
    assert Test().to_binary() == bytes([0b00110100, 129, 0b00110100, 250])


def test_ADDC_at():
    class Test(Program):
        def main(self):
            addc(at(R0))
    assert Test().to_binary() == bytes([0b00110110])


def test_AJMP():
    class Test(Program):
        def main(self):
            ajmp(42)
            ajmp(2000)
    assert Test().to_binary() == bytes([
        0b00000001, 0b00101010,
        0b11100001, 0b11010000
    ])


@mark.xfail(reason="TODO: kwargs and alternatives don’t work together yet.")
def test_AJMP_kwargs():
    class Test(Program):
        def main(self):
            ajmp(addr16=42)
    assert Test().to_binary() == bytes([
        0b00000001, 0b00101010,
    ])


def test_AJMP_fails_with_negative_argument():
    class Test(Program):
        def main(self):
            ajmp(-42)
    with raises(WrongSignatureException):
        Test().to_binary()


def test_AJMP_different_blocks():
    class Test(Program):
        def main(self):
            ajmp(3000)
    with raises(ValueError):
        Test().to_binary()

    class Test(Program):
        def main(self):
            for _ in range(2 ** 11 - 4):
                nop()
            ajmp(2 ** 11 + 2)
            for _ in range(20):
                nop()
    with raises(ValueError):
        Test().to_binary()


def test_SJMP_label():
    class Test(Program):
        def main(self):
            Label("begin")
            sjmp("begin")

    assert Test().to_binary() == bytes([0b10000000, 0b11111110])



def test_AND():
    class Test(Program):
        def main(self):
            andl(R3)
            andl(Byte(111))
            # AND direct, A
            andl(Byte(123), A)
            # AND direct, immediate
            andl(Byte(100), -42)
    assert Test().to_binary() == bytes([
        0b01011011,
        0b01010101, 111,
        0b01010010, 123,
        0b01010011, 100, 214,
    ])


def test_CLR_A():
    class Test(Program):
        def main(self):
            clr()
    assert Test().to_binary() == bytes([0b11100100])


def test_INC():
    class Test(Program):
        def main(self):
            inc()
            inc(R7)
            inc(Byte(42))
            inc(at(R0))
            inc(DPTR)
    assert Test().to_binary() == bytes([
        0b00000100,
        0b00001111,
        0b00000101,
        42,
        0b00000110,
        0b10100011
    ])


def test_repr():
    add_ = None
    class Test(Program):
        def main(self):
            nonlocal add_
            add_ = add(at(R1))
    Test().to_binary()
    assert repr(add_) == "add(indirect=IR1)"

    class Test(Program):
        def main(self):
            nonlocal add_
            add_ = add(direct=Byte(42))
    Test().to_binary()
    assert repr(add_) == "add(direct=Byte(42))"


def test_pop_acc():
    class Test(Program):
        def main(self):
            pop(A)

    assert Test().to_binary() == bytes([0b1101_0000, 0xe0])


def test_pop_register():
    class Test(Program):
        def main(self):
            pop(R1)

    assert Test().to_binary() == bytes([0b1101_0000, 0x01])
