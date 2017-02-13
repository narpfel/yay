from pytest import raises, fixture, importorskip, mark

from yay import Program
from yay.cpu import make_cpu


@fixture
def Foo():
    class Foo(Program, cpu="AT89S8253"):
        def main(self):
            with raises(AttributeError):
                R0.not_existing_attribute
            R0.not_existing_attribute = 42
    return Foo


@fixture
def Bar():
    class Bar(Program, cpu="AT89S8253"):
        def main(self):
            with raises(AttributeError):
                R0.not_existing_attribute
            R0.not_existing_attribute = 42
    return Bar


@fixture
def Baz(Foo):
    class Baz(Foo):
        pass
    return Baz


@mark.xfail(reason="TODO: Decide whether this should fail. Preference: Yes.")
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
        make_cpu("AT89S8253")["registers"]["R0"].not_existing_attribute
