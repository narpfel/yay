from pathlib import Path
from textwrap import dedent
import functools
import itertools
import decimal

from yay.cpu import make_cpu, read_cpu_config
from yay.helpers import config_filename


# Very crude, but this tests whether `make_cpu` finds the same file regardless
# of how it is called.
def test_make_cpu():
    assert make_cpu(
        Path(config_filename("cpu_configurations/AT89S8253.yml"))
    ).keys() == make_cpu("AT89S8253").keys()


def test_read_cpu_config_import(tmpdir):
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

    assert read_cpu_config(test_yml.strpath) == {
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


def test_call_many(tmpdir):
    test_yml = tmpdir.join("test_call_many.yml")
    test_yml.write(dedent(
        """
        foo:
            import: "sub"
            call_many:
                bar: ["b", "a", "bar"]
                foo: ["f", "b", "foo"]
        bar:
            import: "sub"
            with_key: true
            call_many:
                b: ["a", "bar"]
                f: ["b", "foo"]
        importing:
            foo: "re"
            bar: "re"
        """
    ))
    assert read_cpu_config(test_yml.strpath) == {
        "foo": {
            "bar": "aar",
            "foo": "boo"
        },
        "bar": {
            "b": "aar",
            "f": "boo"
        }
    }
