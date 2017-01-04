from contextlib import contextmanager
from functools import lru_cache
from subprocess import call
from textwrap import dedent

from pytest import raises, mark

from yay.program import Program as _Program, block_macro, macro, sub


class Program(_Program, cpu="AT89S8253"):
    pass


@lru_cache(maxsize=1)
def has_sdcc():
    try:
        call(["sdas8051"])
        call(["sdobjcopy"])
        call(["sdld"])
    except FileNotFoundError:
        return False
    else:
        return True


def test_for_loop():
    class Test(Program):
        @block_macro
        def my_loop(self, register, n):
            MOV(register, n)
            Label("loop_head")
            yield
            DJNZ(register, "loop_head")

        def main(self):
            CLR()
            with self.my_loop(R7, 5):
                ADD(R7)

    # This shall expand to:
    class Expected(Program):
        def main(self):
            CLR()
            MOV(R7, 5)
            Label("loop_head")
            ADD(R7)
            DJNZ(R7, "loop_head")

    assert Test().to_binary() == Expected().to_binary()


def test_default_for_loop():
    class Test(Program):
        def main(self):
            CLR()
            with self.loop(R7, 5):
                ADD(R7)

    class Expected(Program):
        def main(self):
            CLR()
            MOV(R7, 5)
            Label("loop_head")
            ADD(R7)
            DJNZ(R7, "loop_head")

    assert Test().to_binary() == Expected().to_binary()


def test_inherited_macros():
    class Base(Program):
        @macro
        def base_macro(self, direct):
            ADD(direct)

    class Test(Base):
        @macro
        def macro(self, direct):
            ADD(direct)

        def main(self):
            self.base_macro(42)
            self.macro(43)

    class Expected(Program):
        def main(self):
            ADD(42)
            ADD(43)

    assert Test().to_binary() == Expected().to_binary()


def test_sub():
    class Test(Program):
        @sub
        def foo(self):
            INC()
            RET()

        def main(self):
            NOP()
            self.foo()
            NOP()

    class Expected(Program):
        def main(self):
            NOP()
            LCALL("foo")
            NOP()
            Label("foo")
            INC()
            RET()

    assert Test().to_binary() == Expected().to_binary()


def test_unused_sub_does_not_emit_body():
    class Test(Program):
        @sub
        def unused(self):
            INC()

        def main(self):
            pass

    assert Test().to_binary() == b""


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


def test_missing_self_fails():
    class Test(Program):
        def main():
            pass
    test = Test()

    with raises(TypeError):
        test.to_binary()


def test_label_used_before_declared():
    class Test(Program):
        def main(self):
            SJMP("label")
            Label("label")

    assert Test().to_binary() == bytes([0b10000000, 0b00000000])


@mark.skipif(not has_sdcc(), reason="sdcc not found on `$PATH`.")
def test_compare_with_sdcc(tmpdir):
    class Test(_Program, cpu="MCS_51"):
        def main(self):
            dir = Byte(42)
            imm = -42
            Rn = R3
            Ri = R0
            rel = "rel"
            addr11 = "rel"
            addr16 = 12345
            bit = Bit(42)

            # Arithmetic operations
            ADD(dir)
            ADD(at(Ri))
            ADD(Rn)
            ADD(imm)
            ADDC(dir)
            ADDC(at(Ri))
            ADDC(Rn)
            ADDC(imm)
            SUBB(dir)
            SUBB(at(Ri))
            SUBB(Rn)
            SUBB(imm)
            INC()
            INC(dir)
            INC(at(Ri))
            INC(Rn)
            INC(DPTR)
            DEC()
            DEC(dir)
            DEC(at(Ri))
            DEC(Rn)
            MUL()
            DIV()
            DA()
            # Logical operations
            AND(dir)
            AND(at(Ri))
            AND(Rn)
            AND(imm)
            AND(dir, A)
            AND(dir, imm)
            OR(dir)
            OR(at(Ri))
            OR(Rn)
            OR(imm)
            OR(dir, A)
            OR(dir, imm)
            XOR(dir)
            XOR(at(Ri))
            XOR(Rn)
            XOR(imm)
            XOR(dir, A)
            XOR(dir, imm)
            CLR()
            CPL()
            RL()
            RLC()
            RR()
            RRC()
            SWAP()
            # Data transfer operations
            LDR(Rn)
            LDD(dir)
            LDR(at(Ri))
            LDI(imm)
            STR(Rn)
            MOV(Rn, dir)
            MOV(Rn, imm)
            STD(dir)
            MOV(dir, Rn)
            MOV(dir, dir)
            MOV(dir, at(Ri))
            MOV(dir, imm)
            STR(at(Ri))
            MOV(at(Ri), dir)
            MOV(at(Ri), imm)
            MOV(DPTR, addr16)
            LPM(at(A + DPTR))
            LPM(at(A + PC))
            LDX(at(Ri))
            LDX(at(DPTR))
            STX(at(Ri))
            STX(at(DPTR))
            PUSH(dir)
            POP(dir)
            XCH(A, dir)
            XCH(A, at(Ri))
            XCH(A, Rn)
            XCHD(A, at(Ri))
            # Boolean operations
            CLR(C)
            CLR(bit)
            SET(C)
            SET(bit)
            CPL(C)
            CPL(bit)
            AND(bit)
            AND(~bit)
            OR(bit)
            OR(~bit)
            LDB(bit)
            STB(bit)

            Label(rel)

            JC(rel)
            JNC(rel)
            JB(bit, rel)
            JNB(bit, rel)
            JBC(bit, rel)
            # Control flow
            # TODO: CALL
            ACALL(addr11)
            LCALL(addr16)
            RET()
            RETI()
            # TODO: JMP
            AJMP(addr11)
            LJMP(addr16)
            SJMP(rel)
            JMP(at(A + DPTR))
            JZ(rel)
            JNZ(rel)
            CJNE(A, dir, rel)
            CJNE(A, imm, rel)
            CJNE(Rn, imm, rel)
            CJNE(at(Ri), imm, rel)
            DJNZ(Rn, rel)
            DJNZ(dir, rel)

            NOP()

    yay_result = Test().to_binary()

    sdcc_asm_source = dedent("""
        ; Arithmetic operations
        ADD A, dir
        ADD A, @Ri
        ADD A, Rn
        ADD A, #imm
        ADDC A, dir
        ADDC A, @Ri
        ADDC A, Rn
        ADDC A, #imm
        SUBB A, dir
        SUBB A, @Ri
        SUBB A, Rn
        SUBB A, #imm
        INC A
        INC dir
        INC @Ri
        INC Rn
        INC DPTR
        DEC A
        DEC dir
        DEC @Ri
        DEC Rn
        MUL AB
        DIV AB
        DA A
        ; Logical operations
        ANL A, dir
        ANL A, @Ri
        ANL A, Rn
        ANL A, #imm
        ANL dir, A
        ANL dir, #imm
        ORL A, dir
        ORL A, @Ri
        ORL A, Rn
        ORL A, #imm
        ORL dir, A
        ORL dir, #imm
        XRL A, dir
        XRL A, @Ri
        XRL A, Rn
        XRL A, #imm
        XRL dir, A
        XRL dir, #imm
        CLR A
        CPL A
        RL A
        RLC A
        RR A
        RRC A
        SWAP A
        ; Data transfer operations
        MOV A, Rn
        MOV A, dir
        MOV A, @Ri
        MOV A, #imm
        MOV Rn, A
        MOV Rn, dir
        MOV Rn, #imm
        MOV dir, A
        MOV dir, Rn
        MOV dir, dir
        MOV dir, @Ri
        MOV dir, #imm
        MOV @Ri, A
        MOV @Ri, dir
        MOV @Ri, #imm
        MOV DPTR, #addr16
        MOVC A, @A+DPTR
        MOVC A, @A+PC
        MOVX A, @Ri
        MOVX A, @DPTR
        MOVX @Ri, A
        MOVX @DPTR, A
        PUSH dir
        POP dir
        XCH A, dir
        XCH A, @Ri
        XCH A, Rn
        XCHD A, @Ri
        ; Boolean operations
        CLR C
        CLR bit
        SETB C
        SETB bit
        CPL C
        CPL bit
        ANL C, bit
        ANL C, /bit
        ORL C, bit
        ORL C, /bit
        MOV C, bit
        MOV bit, C

rel:

        JC rel
        JNC rel
        JB bit, rel
        JNB bit, rel
        JBC bit, rel
        ; Control flow operations
        ; TODO: CALL
        ACALL addr11
        LCALL addr16
        RET
        RETI
        ; TODO: JMP
        AJMP addr11
        LJMP addr16
        SJMP rel
        JMP @A+DPTR
        JZ rel
        JNZ rel
        CJNE A, dir, rel
        CJNE A, #imm, rel
        CJNE Rn, #imm, rel
        CJNE @Ri, #imm, rel
        DJNZ Rn, rel
        DJNZ dir, rel

        NOP
    """
        .replace("dir", "42")
        .replace("imm", "-42")
        .replace("Rn", "R3")
        .replace("Ri", "R0")
        .replace("addr11", "rel")
        .replace("addr16", "12345")
        .replace("bit", "42")
    )

    asm_source_file = tmpdir.join("expected.a51")
    rel_file = tmpdir.join("expected.rel")
    ihex_file = tmpdir.join("expected.ihx")
    bin_file = tmpdir.join("expected.bin")
    asm_source_file.write(sdcc_asm_source)

    assert call(["sdas8051", "-o", asm_source_file.strpath]) == 0
    assert call(["sdld", "-i", rel_file.strpath]) == 0
    assert call([
        "sdobjcopy",
        "-O", "binary",
        "-I", "ihex",
        ihex_file.strpath,
        bin_file.strpath
    ]) == 0

    assert bin_file.read_binary() == yay_result


def test_program_relocation():
    class Test(Program):
        def main(self):
            INC()

    test = Test()
    test.relocate(0x8000)

    not_relocated = Test()

    assert test.to_binary() == b"\0" * 0x8000 + not_relocated.to_binary()
