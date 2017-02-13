from contextlib import contextmanager
from functools import lru_cache
from subprocess import call
from textwrap import dedent

from pytest import raises, mark

from yay import Program as _Program, block_macro, macro, sub


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
            mov(register, n)
            Label("loop_head")
            yield
            djnz(register, "loop_head")

        def main(self):
            clr()
            with self.my_loop(R7, 5):
                add(R7)

    # This shall expand to:
    class Expected(Program):
        def main(self):
            clr()
            mov(R7, 5)
            Label("loop_head")
            add(R7)
            djnz(R7, "loop_head")

    assert Test().to_binary() == Expected().to_binary()


def test_default_for_loop():
    class Test(Program):
        def main(self):
            clr()
            with self.loop(R7, 5):
                add(R7)

    class Expected(Program):
        def main(self):
            clr()
            mov(R7, 5)
            Label("loop_head")
            add(R7)
            djnz(R7, "loop_head")

    assert Test().to_binary() == Expected().to_binary()


def test_inherited_macros():
    class Base(Program):
        @macro
        def base_macro(self, direct):
            add(direct)

    class Test(Base):
        @macro
        def macro(self, direct):
            add(direct)

        def main(self):
            self.base_macro(42)
            self.macro(43)

    class Expected(Program):
        def main(self):
            add(42)
            add(43)

    assert Test().to_binary() == Expected().to_binary()


def test_sub():
    class Test(Program):
        @sub
        def foo(self):
            inc()

        def main(self):
            nop()
            self.foo()
            nop()

    class Expected(Program):
        def main(self):
            nop()
            lcall("foo")
            nop()
            Label("foo")
            inc()
            ret()

    assert Test().to_binary() == Expected().to_binary()


def test_unused_sub_does_not_emit_body():
    class Test(Program):
        @sub
        def unused(self):
            inc()

        def main(self):
            pass

    assert Test().to_binary() == b""


@mark.xfail(reason="Not sure if this should be implemented.")
def test_opcodes_in_class_body():
    class InBody(Program):
        add(R2)


    class InMain(Program):
        def main(self):
            add(R2)

    assert InBody().to_binary() == InMain().to_binary()


def test_opcodes_in_class_body_fail():
    with raises(NameError):
        class Test(Program):
            add(R3)


def test_self():
    class Test(Program):
        foo = 42
        def main(self):
            add(R3)
            add(42)
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
            sjmp("label")
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
            add(dir)
            add(at(Ri))
            add(Rn)
            add(imm)
            addc(dir)
            addc(at(Ri))
            addc(Rn)
            addc(imm)
            subb(dir)
            subb(at(Ri))
            subb(Rn)
            subb(imm)
            inc()
            inc(dir)
            inc(at(Ri))
            inc(Rn)
            inc(DPTR)
            dec()
            dec(dir)
            dec(at(Ri))
            dec(Rn)
            mul()
            div()
            da()
            # Logical operations
            andl(dir)
            andl(at(Ri))
            andl(Rn)
            andl(imm)
            andl(dir, A)
            andl(dir, imm)
            orl(dir)
            orl(at(Ri))
            orl(Rn)
            orl(imm)
            orl(dir, A)
            orl(dir, imm)
            xor(dir)
            xor(at(Ri))
            xor(Rn)
            xor(imm)
            xor(dir, A)
            xor(dir, imm)
            clr()
            cpl()
            rl()
            rlc()
            rr()
            rrc()
            swap()
            # Data transfer operations
            ldr(Rn)
            ldd(dir)
            ldr(at(Ri))
            ldi(imm)
            str(Rn)
            mov(Rn, dir)
            mov(Rn, imm)
            std(dir)
            mov(dir, Rn)
            mov(dir, dir)
            mov(dir, at(Ri))
            mov(dir, imm)
            str(at(Ri))
            mov(at(Ri), dir)
            mov(at(Ri), imm)
            mov(DPTR, addr16)
            lpm(at(A + DPTR))
            lpm(at(A + PC))
            ldx(at(Ri))
            ldx(at(DPTR))
            stx(at(Ri))
            stx(at(DPTR))
            push(dir)
            pop(dir)
            xch(A, dir)
            xch(A, at(Ri))
            xch(A, Rn)
            xchd(A, at(Ri))
            # Boolean operations
            clr(C)
            clr(bit)
            set(C)
            set(bit)
            cpl(C)
            cpl(bit)
            andl(bit)
            andl(~bit)
            orl(bit)
            orl(~bit)
            ldb(bit)
            stb(bit)

            Label(rel)

            jc(rel)
            jnc(rel)
            jb(bit, rel)
            jnb(bit, rel)
            jbc(bit, rel)
            # Control flow
            # TODO: CALL
            acall(addr11)
            lcall(addr16)
            ret()
            reti()
            # TODO: JMP
            ajmp(addr11)
            ljmp(addr16)
            sjmp(rel)
            jmp(at(A + DPTR))
            jz(rel)
            jnz(rel)
            cjne(A, dir, rel)
            cjne(A, imm, rel)
            cjne(Rn, imm, rel)
            cjne(at(Ri), imm, rel)
            djnz(Rn, rel)
            djnz(dir, rel)

            nop()

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
            inc()

    test = Test()
    test.relocate(0x8000)

    not_relocated = Test()

    assert test.to_binary() == b"\0" * 0x8000 + not_relocated.to_binary()
