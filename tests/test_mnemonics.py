from pytest import raises

from yay.program import Program as _Program
from yay.helpers import InvalidRegisterError, WrongSignatureException


class Program(_Program, cpu="AT89S8253"):
    pass


def test_insert_in_opcodes():
    add, and_ = None, None
    class Test(Program):
        def main(self):
            nonlocal add, and_
            add = ADD(R3)
            and_ = AND(42)
    test = Test()
    binary = test.to_binary()
    assert add is not None
    assert and_ is not None
    assert test._opcodes == [add, and_]
    assert binary == b"".join([add.opcode, and_.opcode])


def test_ACALL():
    class Test(Program):
        def main(self):
            acall = ACALL(addr11=1234)
    assert Test().to_binary() == bytes([0b10010001, 0b11010010])


def test_ADD():
    class Test(Program):
        def main(self):
            ADD(R3)
            ADD(Byte(42))
    assert Test().to_binary() == bytes([0b00101011, 0b00100101, 42])


    class Test(Program):
        def main(self):
            ADD(R3, A)
    with raises(WrongSignatureException):
        Test().to_binary()

    class Test(Program):
        def main(self):
            ADD(42, A)
    with raises(WrongSignatureException):
        Test().to_binary()


def test_ADD_at():
    class Test(Program):
        def main(self):
            ADD(at(R1))
    assert Test().to_binary() == bytes([0b00100111])

    class Test(Program):
        def main(self):
            ADD(at(R4))
    with raises(InvalidRegisterError):
        Test().to_binary()

    class Test(Program):
        def main(self):
            ADD(at(1))
    with raises(TypeError):
        Test().to_binary()

    class Test(Program):
        def main(self):
            ADD(at(R1), A)
    with raises(TypeError):
        Test().to_binary()

    class Test(Program):
        def main(self):
            ADD(at(42), A)
    with raises(TypeError):
        Test().to_binary()


def test_ADD_immediate():
    class Test(Program):
        def main(self):
            ADD(42)
    assert Test().to_binary() == bytes([0b00100100, 42])

    class Test(Program):
        def main(self):
            ADD(420)
    with raises(WrongSignatureException):
        Test().to_binary()

    class Test(Program):
        def main(self):
            ADD(42, A)
    with raises(TypeError):
        Test().to_binary()

    class Test(Program):
        def main(self):
            ADD(R1, A)
    with raises(TypeError):
        Test().to_binary()


def test_ADDC():
    class Test(Program):
        def main(self):
            ADDC(R7)
            ADDC(Byte(127))

    assert Test().to_binary() == bytes(
        [0b00111111, 0b00110101, 127]
    )

    class Test(Program):
        def main(self):
            ADDC(-127)
            ADDC(250)
    assert Test().to_binary() == bytes([0b00110100, 129, 0b00110100, 250])


def test_ADDC_at():
    class Test(Program):
        def main(self):
            ADDC(at(R0))
    assert Test().to_binary() == bytes([0b00110110])


def test_AJMP():
    class Test(Program):
        def main(self):
            AJMP(42)
            AJMP(2000)
    assert Test().to_binary() == bytes([
        0b00000001, 0b00101010,
        0b11100001, 0b11010000
    ])


def test_AJMP_overflow():
    class Test(Program):
        def main(self):
            AJMP(3000)
    with raises(WrongSignatureException):
        Test().to_binary()


def test_AJMP_fails_with_negative_argument():
    class Test(Program):
        def main(self):
            AJMP(-42)
    with raises(WrongSignatureException):
        Test().to_binary()


def test_AND():
    class Test(Program):
        def main(self):
            AND(R3)
            AND(Byte(111))
            # AND direct, A
            AND(Byte(123), A)
            # AND direct, immediate
            AND(Byte(100), -42)
    assert Test().to_binary() == bytes([
        0b01011011,
        0b01010101, 111,
        0b01010010, 123,
        0b01010011, 100, 214,
    ])


def test_CLR_A():
    class Test(Program):
        def main(self):
            CLR()
    assert Test().to_binary() == bytes([0b11100100])


def test_INC():
    class Test(Program):
        def main(self):
            INC()
            INC(R7)
            INC(Byte(42))
            INC(at(R0))
            INC(DPTR)
    assert Test().to_binary() == bytes([
        0b00000100,
        0b00001111,
        0b00000101,
        42,
        0b00000110,
        0b10100011
    ])
