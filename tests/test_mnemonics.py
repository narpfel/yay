from pytest import fixture, raises, mark

from yay.program import Program, ProgramMeta
from yay.helpers import InvalidRegisterError, WrongSignatureException


def test_insert_in_opcodes():
    add, and_ = None, None
    class Test(Program):
        def main():
            nonlocal add, and_
            add = ADD(R3)
            and_ = AND(42)
    test = Test()
    binary = test.to_binary()
    assert add is not None
    assert and_ is not None
    assert test._opcodes == [add, and_]
    assert binary == b"".join([add.opcode, and_.opcode])


@mark.xfail(reason="Not implemented yet.")
def test_immediate():
    class Test(Program):
        def main():
            ADD(immediate(250))

    class Expected(Program):
        def main():
            ADDI(250)

    assert Test().to_binary() == Expected().to_binary()


def test_ACALL():
    class Test(Program):
        def main():
            acall = ACALL(addr11=1234)
    assert Test().to_binary() == bytes([0b10010001, 0b11010010])


def test_ADD():
    class Test(Program):
        def main():
            ADD(R3)
            ADD(42)
    assert Test().to_binary() == bytes([0b00101011, 0b00100101, 42])


    class Test(Program):
        def main():
            ADD(R3, A)
    with raises(WrongSignatureException):
        Test().to_binary()

    class Test(Program):
        def main():
            ADD(42, A)
    with raises(WrongSignatureException):
        Test().to_binary()


def test_ADD_at():
    class Test(Program):
        def main():
            ADD(at(R1))
    assert Test().to_binary() == bytes([0b00100111])

    class Test(Program):
        def main():
            ADD(at(R4))
    with raises(InvalidRegisterError):
        Test().to_binary()

    class Test(Program):
        def main():
            ADD(at(1))
    with raises(TypeError):
        Test().to_binary()

    class Test(Program):
        def main():
            ADD(at(R1), A)
    with raises(TypeError):
        Test().to_binary()

    class Test(Program):
        def main():
            ADD(at(42), A)
    with raises(TypeError):
        Test().to_binary()


def test_ADDI():
    class Test(Program):
        def main():
            ADDI(42)
    assert Test().to_binary() == bytes([0b00100100, 42])

    class Test(Program):
        def main():
            ADDI(420)
    with raises(WrongSignatureException):
        Test().to_binary()

    class Test(Program):
        def main():
            ADDI(42, A)
    with raises(TypeError):
        Test().to_binary()

    class Test(Program):
        def main():
            ADDI(R1, A)
    with raises(TypeError):
        Test().to_binary()

    class Test(Program):
        def main():
            ADDI(R1)
    with raises(TypeError):
        Test().to_binary()

    class Test(Program):
        def main():
            ADDI(at(R0))
    with raises(TypeError):
        Test().to_binary()


def test_ADDC():
    class Test(Program):
        def main():
            ADDC(R7)
            ADDC(127)

    assert Test().to_binary() == bytes(
        [0b00111111, 0b00110101, 127]
    )

    class Test(Program):
        def main():
            ADDC(-127)
    with raises(WrongSignatureException):
        Test().to_binary()


def test_ADDC_at():
    class Test(Program):
        def main():
            ADDC(at(R0))
    assert Test().to_binary() == bytes([0b00110110])


def test_ADDCI():
    class Test(Program):
        def main():
            ADDCI(-127)
            ADDCI(250)
    assert Test().to_binary() == bytes([0b00110100, 129, 0b00110100, 250])


def test_AJMP():
    class Test(Program):
        def main():
            AJMP(42)
            AJMP(2000)
    assert Test().to_binary() == bytes([
        0b00000001, 0b00101010,
        0b11100001, 0b11010000
    ])


def test_AJMP_overflow():
    class Test(Program):
        def main():
            AJMP(3000)
    with raises(WrongSignatureException):
        Test().to_binary()


def test_AJMP_fails_with_negative_argument():
    class Test(Program):
        def main():
            AJMP(-42)
    with raises(WrongSignatureException):
        Test().to_binary()


def test_AND():
    class Test(Program):
        def main():
            AND(R3)
            AND(111)
            # AND direct, A
            AND(123, A)
            # AND direct, immediate
            AND(100, -42)
    assert Test().to_binary() == bytes([
        0b01011011,
        0b01010101, 111,
        0b01010010, 123,
        0b01010011, 100, 214,
    ])


def test_CLR_A():
    class Test(Program):
        def main():
            CLR()
    assert Test().to_binary() == bytes([0b11100100])
