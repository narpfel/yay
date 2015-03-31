from textwrap import dedent
import functools
import itertools
import decimal

from pytest import raises

from yay.helpers import reverse_dict, twos_complement, read_config


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


def test_read_config_import(tmpdir):
    test_yml = tmpdir.join("test.yml")
    test_yml.write(dedent(
        """
        foo:
            bar:
                from: "functools"
                import: "wraps"
            baz:
                from: "decimal"
                import: "Decimal"
                call: [42]
            test:
                import: "count"
            parrot: 42
        bar:
            answer:
                import: "add"
                call: [20, 22]
            spam:
                import: "mul"
                call: ["a", 42]
            parrot: "foo"
        without_imports:
            answer: 42
            spam: "parrot"
            parrot:
                from: "itertools"
                import: "chain"
        importing:
            foo: "itertools"
            bar: "operator"
        """
    ))

    assert read_config(test_yml.strpath) == {
        "foo": {
            "bar": functools.wraps,
            "baz": decimal.Decimal(42),
            "test": itertools.count,
            "parrot": 42,
        },
        "bar": {
            "answer": 42,
            "spam": "a" * 42,
            "parrot": "foo",
        },
        "without_imports": {
            "answer": 42,
            "spam": "parrot",
            "parrot": {
                "from": "itertools",
                "import": "chain",
            },
        }
    }
