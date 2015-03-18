from pytest import raises, fixture, importorskip, mark

from yay.program import _Program
from yay.cpu import AT89S8253


pytestmark = mark.xfail(reason="Not implemented yet.")


@fixture
def Foo():
    class Foo(_Program, cpu=AT89S8253):
        def main():
            with raises(AttributeError):
                R0.not_existing_attribute
            R0.not_existing_attribute = 42
    return Foo


@fixture
def Bar():
    class Bar(_Program, cpu=AT89S8253):
        def main():
            with raises(AttributeError):
                R0.not_existing_attribute
            R0.not_existing_attribute = 42
    return Bar


@fixture
def Baz(Foo):
    class Baz(Foo):
        pass
    return Baz


def test_multiple_to_binary_call(Foo):
    foo = Foo()
    foo.to_binary()
    foo.to_binary()


def test_multiple_instantiation(Foo):
    Foo().to_binary()
    Foo().to_binary()


def test_different_classes_are_isolated(Foo, Bar):
    Foo().to_binary()
    Bar().to_binary()


def test_inherited_classes_are_isolated(Foo, Baz):
    Foo().to_binary()
    Baz().to_binary()


def test_cpu_unaffected(Foo):
    Foo().to_binary()
    with raises(AttributeError):
        AT89S8253.registers["R0"].not_existing_attribute
