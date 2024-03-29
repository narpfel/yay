from textwrap import dedent

from pytest import raises

from yay.helpers import (
    read_config, recursive_merge, reverse_dict, twos_complement
)


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


def test_read_config(tmpdir):
    test_yml = tmpdir.join("test.yml")
    test_yml.write(dedent(
        """
        test_key: test_value
        """
    ))
    assert read_config(test_yml.strpath) == {"test_key": "test_value"}


def test_recursive_merge():
    assert recursive_merge({
        "foo": "bar",
        "parrot": {
            "spam": 7,
            "cheese": {
                "foo": 42,
                "bar": 7
            }
        },
        "not_updated": 22
    }, {
        "foo": "spam",
        "parrot": {
            "cheese": {
                "bar": 42,
                "yummy": "ham and eggs"
            },
            42: 7
        }
    }) == {
        "foo": "spam",
        "parrot": {
            "spam": 7,
            "cheese": {
                "foo": 42,
                "bar": 42,
                "yummy": "ham and eggs"
            },
            42: 7
        },
        "not_updated": 22
    }
