from yay import Program

class Main(Program, cpu="MCS_51"):
    def main(self):
        mov(R0, 42)


R0 = 12


def test_global_name_does_not_shadow_injected_name():
    assert Main().to_binary() == bytes([0b0111_1000, 0b0010_1010])
