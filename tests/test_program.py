from contextlib import contextmanager

from pytest import raises, mark

from yay.program import Program as _Program


class Program(_Program, cpu="AT89S8253"):
    pass


try:
    class Test(Program):
        macro
        sub
except NameError:
    should_skip = True
else:
    should_skip = False


@mark.skipif(should_skip, reason="Macros and subs not implemented.")
def test_mnemonics_in_method():
    class Test(Program):
        @macro
        def add_and(self, operand):
            """
            ``@macro``s should just expand to their assembled opcodes where
            they are called. They should provide arguments and lexical scoping,
            especially for labels. This is important! It must never be possible
            to jump from `main` to a label defined in in a macro inserted in
            `main`.
            """
            ADD(operand)
            AND(operand)

        @sub
        def adda(self, operand):
            """
            ``@sub``s shall expand to `CALL; {sub}; RET` except they
            end in ``tail_call(sub)`` (or are decorated with ``@tail_call``).
            (This is yet to be decided, preference in ``tail_call(other_sub)``.)
            Then they shall `JMP` to the tail called sub.

            TODO: Calling conventions: what does `operand` mean‽ How does the
            required information get from the caller to the calee?
            """
            ADDA(operand)

        def main(self):
            CLR(A)
            ADD(R3)
            ADD(42)
            add_and(12)
            CLR(A)
            add_and(R2)
            CLR(A)
            adda(R1)
            # This shall expand to:
            #
            # LABEL("adda")
            # ADDA({operand})
            # RET
            # LABEL("main") # This is where the program starts.
            # CLR(A)
            # ADD(R3)
            # ADD(42)
            # ADD(12)
            # AND(12)
            # CLR(A)
            # ADD(R2)
            # AND(R2)
            # CLR(A)
            # CALL("adda")

    test = Test()
    assert False # Add correct binary below.
    # `Test.to_binary` shall invoke `main` and spit out the complete program
    # in binary, (in theory) ready to be programmed.
    assert test.to_binary() == bytes([0b00101011, 0b00100101, 42])


@mark.skipif(should_skip, reason="Macros and subs not implemented yet.")
def test_for_loop():
    class Test(Program):
        @macro
        @contextmanager
        def loop(self, register, n):
            """Actual loop implementation?"""
            MOVI(register, n)
            LABEL("loop_head")
            yield
            DJNZ(register, "loop_head")

        def main(self):
            CLR(A)
            with loop(R7, 5):
                ADD(R7)

            # This shall expand to
            #
            # CLR(A)
            # MOV(register, n)
            # LABEL("loop_head")
            # ADD(A, R7)
            # DJNZ(R7, "loop_head")

    assert False


@mark.xfail(reason="Not sure if this should be implemented.")
def test_opcodes_in_class_body():
    class InBody(Program):
        ADD(R2)


    class InMain(Program):
        def main(self):
            ADD(R2)

    assert InBody().to_binary() == InMain().to_binary()


def test_opcodes_in_class_body_fail():
    with raises(NameError):
        class Test(Program):
            ADD(R3)


def test_self():
    class Test(Program):
        foo = 42
        def main(self):
            ADD(R3)
            ADD(42)
            with raises(NameError):
                foo
            self.foo
    Test().to_binary()
