from pytest import raises

from yay.helpers import reverse_dict, twos_complement


def test_reverse_dict():
    assert reverse_dict({1: 2, 3: 4}) == {2: 1, 4: 3}
    with raises(ValueError):
        reverse_dict({1: 2, 3: 2})
    with raises(TypeError):
        reverse_dict({42: [1, 2, 3]})


def test_twos_complement():
    assert twos_complement(-127, 8) == 129
    assert twos_complement(42, 8) == 42
    assert twos_complement(250, 8) == 250
    assert twos_complement(-42, 8) == 214
    with raises(ValueError):
        twos_complement(-129, 8)
    with raises(ValueError):
        twos_complement(256, 8)
