from pytest import fixture, raises

from yay import InvalidRegisterError, Program
from yay.cpu import make_cpu
from yay.cpus.MCS_51 import Byte, DptrOffset, at
from yay.mnemonic import Mnemonic


# TODO: Dirty hack!
cpu = make_cpu("AT89S8253")
globals().update(cpu["registers"])
globals().update(cpu["sfrs"])

# TODO for @A+DPTR (also covered by the hack above)
# DPTR = AT89S8253.DPTR
# A = AT89S8253.A


@fixture
def test_mnemonic(mocker):
    mocker.patch("yay.mnemonic.Mnemonic.__init__", return_value=None)
    class TestProgram(Program, cpu="MCS_51"):
        pass
    TestMnemonic = Mnemonic.bind_program(TestProgram())
    return TestMnemonic()


def test_matches_args(test_mnemonic):
    # TODO: Should test `cpus.MCS_51.match_helpers` directly (without
    # mnemonic and program)
    tests = [
        [[R0], ["register"], True],
        [[R0, Byte(42)], ["register"], False],
        [[R0, Byte(42)], ["register", "direct"], True],
        [[R0], ["register", "direct"], False],
        [[-42], ["immediate"], True],
        [[-130], ["immediate"], False],
        [[250], ["immediate"], True],
        [[Byte(-5)], ["direct"], False],
        [[256], ["immediate"], False],
        [[at(R0)], ["indirect"], True],
        [[at(R1)], ["indirect"], True],
        [[R0], ["indirect"], False],
        [[R4], ["indirect"], False],
        [[at(R0)], ["register"], False],
        [[P1], ["direct"], True],
        # Nothing directly matches `relative`
        # TODO: Should be `False`!
        [[120], ["relative"], True],
        [[120], ["addr16"], True]
    ]
    for args, argument_format, expected in tests:
        matches, _ = test_mnemonic.matches_args(args, argument_format)
        assert bool(matches) is expected


def test_int_not_matches_direct(test_mnemonic):
    assert not test_mnemonic.matches_args([42], ["direct"])[0]


def test_at():
    assert at(R0).indirect_number == 0
    assert at(at(R0)) is at(R0)

    with raises(InvalidRegisterError):
        at(R2)


def test_at_DPTR():
    assert isinstance(at(A + DPTR), DptrOffset)


def test_matches_kwargs(test_mnemonic):
    tests = [
        [{"register": R0}, ["register"], True],
        [{"direct": Byte(13), "register": R5}, ["register", "direct"], True],
        [{"indirect": at(R1), "immediate": -14}, ["indirect", "immediate"], True],
        [{"register": R3}, ["immediate"], False],
        [{"direct": Byte(-42)}, ["direct"], False],
        [{"immediate": 512}, ["immediate"], False],
    ]

    for kwargs, argument_format, expected in tests:
        matches, _ = test_mnemonic.matches_kwargs(kwargs, argument_format)
        assert bool(matches) is expected
