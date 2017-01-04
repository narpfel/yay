from pytest import fixture

from yay.program import Program


@fixture
def TestProgram():
    class TestProgram(Program, cpu="MCS_51"):
        def main(self):
            Label("before_nop")
            nop()
            Label("after_nop")

    return TestProgram


def test_label_no_output(TestProgram):
    assert TestProgram().to_binary() == b"\0"


def test_label_at_right_positions(TestProgram):
    test = TestProgram()
    test.to_binary()
    assert test.labels["before_nop"] == 0
    assert test.labels["after_nop"] == 1
