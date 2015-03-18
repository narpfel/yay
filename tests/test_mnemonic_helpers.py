import pytest
from pytest import raises

from yay.mnemonics import matches_args, matches_kwargs
from yay.registers import AT89S8253, at, IndirectRegister

from yay.helpers import InvalidRegisterError


globals().update(AT89S8253._registers)

# TODO for @A+DPTR
# DPTR = AT89S8253.DPTR
# A = AT89S8253.A


def test_matches_args():
    tests = [
        [[R0], ["register"], True],
        [[R0, 42], ["register"], False],
        [[R0, 42], ["register", "direct"], True],
        [[R0], ["register", "direct"], False],
        [[-42], ["immediate"], True],
        [[-130], ["immediate"], False],
        [[250], ["immediate"], True],
        [[-5], ["direct"], False],
        [[256], ["immediate"], False],
        [[at(R0)], ["indirect"], True],
        [[at(R1)], ["indirect"], True],
        [[R0], ["indirect"], False],
        [[R4], ["indirect"], False],
        [[at(R0)], ["register"], False],
    ]
    for args, argument_format, expected in tests:
        assert bool(matches_args(args, argument_format)) is expected


def test_at():
    assert at(R0).number == 0
    assert at(R0).indirect is True
    assert at(at(R0)) is at(R0)

    with raises(InvalidRegisterError):
        at(R2)


@pytest.mark.xfail(reason="Not implemented yet.")
def test_at_DPTR():
    assert at(A + DPTR).indirect is True


def test_matches_kwargs():
    tests = [
        [{"register": R0}, ["register"], True],
        [{"direct": 13, "register": R5}, ["register", "direct"], True],
        [{"indirect": at(R1), "immediate": -14}, ["indirect", "immediate"], True],
        [{"register": R3}, ["immediate"], False],
        [{"direct": -42}, ["direct"], False],
        [{"immediate": 512}, ["immediate"], False],
    ]

    for kwargs, argument_format, expected in tests:
        assert bool(matches_kwargs(kwargs, argument_format)) is expected
