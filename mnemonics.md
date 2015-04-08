`yay` Mnemonics
===============

Typographic Conventions
-----------------------

* `{}` → Denotes a variable.
* `#` → Denotes an immediate.
* `Rn` → Any register on the current bank.
* `Ri` → A register that can be used for indirect addressing, i. e. `R0` or
  `R1`.
* `dir` → A direct address.
* `imm` → An immediate.
* `rel` → A relative address (byte), usually a in form of a label.
* `addr` → A generic address, one of `rel`, `addr11`, `addr16`.
* `addr11` → An 11-bit address.
* `addr16` → An absolute 16-bit address.
* `bit` → A direct bit address.
* `/` → Invert.


Notable changes to stock 8051 assembler
---------------------------------------

* `MOV*` has been split up into four different families of mnemonics:
  * `LD*` loads data *into* the accu.
  * `ST*` stores data *from* the accu.
  * `MOV*` operates on registers.
  * `LPM` accesses the program memory.

  Hence, all `LD*`, `ST*` and `LPM` mnemonics take one argument (the
  accumulator) is implicit, whereas `MOV*` operations have *two* operands.

  **TODO:** Decide whether to use the Intel-like form `MOV(destination, source)`
  or the AT&T-like form `MOV(source, destination)`.


### List of `MOV` family mnemonics

| Mnemonic | Effect                       | Equivalent to   |
|:---------|:-----------------------------|:----------------|
| `LDD`    | Load `A` with direct         |                 |
| `STD`    | Store `A` to direct          |                 |
| `LDR`    | Load `A` from register       |                 |
| `STR`    | Store to register            |                 |
| `LDA`    | Load `A` from indirect       |                 |
| `STA`    | Store to indirect            |                 |
| `LDI`    | Load `A` with immediate      | `MOV A, #{imm}` |
| `LPM`    | Load `A` from program memory | `MOVC`          |
| `LDX`    | Load from eXternal memory    | `MOVX A, *`     |
| `STX`    | Store to eXternal memory     | `MOVX *, A`     |
| `LDB`    | Load bit to `C`              |                 |
| `STB`    | Store bit from `C`           |                 |



Indirect addressing
-------------------

Indirect addressing is a bit difficult because in Python you can’t throw `@`
sign in at random places... There are two approaches:

* The macro name denotes whether a register is used for register addressing or
  indirect addressing: `INC(R0)` increments register 0 whereas `INCA(R0)`
  (read “increment *at* `R0`”) increments the content of the memory cell
  pointed to by `R0`.

  This has the disadvantage that you cannot easily decide with compile time
  logic which addressing mode to use. This can come in handy in a macro that
  wants to allow both register and indirect addressing:

  ```python
  @macro
  def increment_twice(register):
      INC(register)
      INC(register)
  ```

  This macro can only increment a register. `increment_twice(R0)` will always
  increment register 0. For indirect addressing, a second macro is necessary:

  ```python
  @macro
  def increment_twice_at(register):
      INCA(register)
      INCA(register)
  ```

* The macro argument denotes the addressing mode: For register addressing just
  the register name is used: `INC(R0)`. For indirect addressing, either the
  register name is wrapped in a call to `at()` or the indirect register name
  is used: `INC(at(R0))` or `INC(IR0)` [^1].

  With this approach `yay` can easily decide at compile time which addressing
  mode to use: `increment_twice(R0)` will increment register 0 twice,
  `increment_twice(at(R0))` will use `R0` as an indirect address.

  **TODO:** `LDA` and `STA` mnemonics would be expressed as `LDR(at(foo))` and
  `STR(at(foo))` which seem a little bit odd.

Currently, the second approach seems to be more advantageous.

[^1]: `IR0` and `IR1` (or `I0` and `I1`) would be synonyms for `at(R0)` and
      `at(R1)`. Not sure if they should be included as they are redundant and
      less explicit.





Complete list of 8051 mnemonics
-------------------------------


| Mnemonic (with operands)     | `yay` equivalent         | `yay` alternative (under consideration)       | Note |
|:-----------------------------|:-------------------------|:----------------------------------------------|:-----|
| **Arithmetic operations**    |                          |                                               |      |
| ``ADD A, {dir}``             | `ADD(dir)`               |                                               |      |
| ``ADD A, @Ri``               | `ADDA(Ri)`               |                                               |      |
| ``ADD A, Rn``                | `ADD(Rn)`                |                                               |      |
| ``ADD A, #{imm}``            | `ADDI(imm)`              |                                               |      |
| ``ADDC A, {dir}``            | `ADDC(dir)`              |                                               |      |
| ``ADDC A, @Ri``              | `ADDCA(Ri)`              |                                               |      |
| ``ADDC A, Rn``               | `ADDC(Rn)`               |                                               |      |
| ``ADDC A, #{imm}``           | `ADDCI(imm)`             |                                               |      |
| ``SUBB A, {dir}``            | `SUBB(dir)`              |                                               |      |
| ``SUBB A, @Ri``              | `SUBBA(Ri)`              |                                               |      |
| ``SUBB A, Rn``               | `SUBB(Rn)`               |                                               |      |
| ``SUBB A, #{imm}``           | `SUBBI(imm)`             |                                               |      |
| `INC A`                      | `INC(A)`                 | `INC()`                                       |      |
| `INC {dir}`                  | `INC(dir)`               |                                               |      |
| `INC @Ri`                    | `INCA(Ri)`               |                                               |      |
| `INC Rn`                     | `INC(Rn)`                |                                               |      |
| `INC DPTR`                   | `INC(DPTR)`              |                                               |      |
| `DEC A`                      | `DEC(A)`                 | `DEC()`                                       |      |
| `DEC {dir}`                  | `DEC(dir)`               |                                               |      |
| `DEC @Ri`                    | `DECA(Ri)`               |                                               |      |
| `DEC Rn`                     | `DEC(Rn)`                |                                               |      |
| `MUL AB`                     | `MUL(A, B)`              | `MUL()`                                       |      |
| `DIV AB`                     | `DIV(A, B)`              | `DIV()`                                       |      |
| `DA A`                       | `DA(A)`                  | `DA()`                                        |      |
| **Logical operations**       |                          |                                               |      |
| `ANL A, {dir}`               | `AND(A, dir)`            | `AND(dir)`                                    | 5    |
| `ANL A, @Ri`                 | `ANDA(A, Ri)`            | `ANDA(Ri)`                                    | 5    |
| `ANL A, Rn`                  | `AND(A, Rn)`             | `AND(Rn)`                                     | 5    |
| `ANL A, #{imm}`              | `ANDI(A, imm)`           | `ANDI(imm)`                                   | 5    |
| `ANL {dir}, A`               | `AND(dir, A)`            |                                               |      |
| `ANL {dir}, #{imm}`          | `ANDI(dir, imm)`         | `AND(dir, imm)`                               |      |
| `ORL A, {dir}`               | `OR(A, dir)`             | `OR(dir)`                                     | 5    |
| `ORL A, @Ri`                 | `ORA(A, Ri)`             | `ORA(Ri)`                                     | 5    |
| `ORL A, Rn`                  | `OR(A, Rn)`              | `OR(Rn)`                                      | 5    |
| `ORL A, #{imm}`              | `ORI(A, imm)`            | `ORI(imm)`                                    | 5    |
| `ORL {dir}, A`               | `OR(dir, A)`             |                                               |      |
| `ORL {dir}, #{imm}`          | `ORI(dir, imm)`          | `OR(dir, imm)`                                |      |
| `XRL A, {dir}`               | `XOR(A, dir)`            |                                               |      |
| `XRL A, @Ri`                 | `XORA(A, Ri)`            |                                               |      |
| `XRL A, Rn`                  | `XOR(A, Rn)`             |                                               |      |
| `XRL A, #{imm}`              | `XORI(A, imm)`           |                                               |      |
| `XRL {dir}, A`               | `XOR(dir, A)`            |                                               |      |
| `XRL {dir}, #{imm}`          | `XORI(dir, imm)`         | `XOR(dir, imm)`                               |      |
| `CLR A`                      | `CLR(A)`                 | `CLR()`                                       |      |
| `CPL A`                      | `CPL(A)`                 | `CPL()`                                       |      |
| `RL A`                       | `RL(A)`                  | `RL()`                                        |      |
| `RLC A`                      | `RLC(A)`                 | `RLC()`                                       |      |
| `RR A`                       | `RR(A)`                  | `RR()`                                        |      |
| `RRC A`                      | `RRC(A)`                 | `RRC()`                                       |      |
| `SWAP A`                     | `SWAP(A)`                | `SWAP()`                                      |      |
| **Data transfer operations** |                          |                                               |      |
| `MOV A, Rn`                  | `LDR(Rn)`                |                                               |      |
| `MOV A, {dir}`               | `LDD(dir)`               |                                               |      |
| `MOV A, @Ri`                 | `LDA(Ri)`                |                                               |      |
| `MOV A, #{imm}`              | `LDI(imm)`               |                                               |      |
| `MOV Rn, A`                  | `STR(Rn)`                |                                               |      |
| `MOV Rn, {dir}`              | `MOV(Rn, dir)`           |                                               |      |
| `MOV Rn, #{imm}`             | `MOVI(Rn, imm)`          |                                               |      |
| `MOV {dir}, A`               | `STD(dir)`               |                                               |      |
| `MOV {dir}, Rn`              | `MOV(dir, Rn)`           |                                               |      |
| `MOV {dir}, {dir}`           | `MOV(dir, dir)`          |                                               |      |
| `MOV {dir}, @Ri`             | `MOVA(dir, Ri)`          |                                               |      |
| `MOV {dir}, #{imm}`          | `MOVI(dir, imm)`         |                                               |      |
| `MOV @Ri, A`                 | `STA(Ri)`                |                                               |      |
| `MOV @Ri, {dir}`             | `MOVA(Ri, dir)`          |                                               |      |
| `MOV @Ri, #{imm}`            | `MOVAI(Ri, imm)`         |                                               |      |
| `MOV DPTR, {addr16}`         | `MOVI(DPTR, addr16)`     |                                               |      |
| `MOVC A, @A+DPTR`            | `LPM(A + DPTR)`          |                                               |      |
| `MOVC A, @A+PC`              | `LPM(A + PC)`            |                                               |      |
| `MOVX A, @Ri`                | `LDX(Ri)`                | `LDXA(Ri)`                                    | 4    |
| `MOVX A, @DPTR`              | `LDX(DPTR)`              | `LDXA(DPTR)`                                  | 4    |
| `MOVX @Ri, A`                | `STX(Ri)`                | `STXA(Ri)`                                    | 4    |
| `MOVX @DPTR, A`              | `STX(DPTR)`              | `STXA(DPTR)`                                  | 4    |
| `PUSH {dir}`                 | `PUSH(dir)`              |                                               |      |
| `POP {dir}`                  | `POP(dir)`               |                                               |      |
| `XCH A, {dir}`               | `XCH(A, dir)`            |                                               |      |
| `XCH A, @Ri`                 | `XCHA(A, Ri)`            |                                               |      |
| `XCH A, Rn`                  | `XCH(A, Rn)`             |                                               |      |
| `XCHD A, @Ri`                | `XCHDA(A, Ri)`           | `XCHD(A, Ri)`                                 | 4    |
| **Boolean operations**       |                          |                                               |      |
| `CLR C`                      | `CLR(C)`                 |                                               |      |
| `CLR {bit}`                  | `CLR(bit)`               |                                               |      |
| `SETB C`                     | `SETB(C)`                | `SETC()`                                      |      |
| `SETB {bit}`                 | `SETB(bit)`              |                                               |      |
| `CPL C`                      | `CPL(C)`                 | `CPLC()`                                      |      |
| `CPL {bit}`                  | `CPL(bit)`               |                                               |      |
| `ANL C, {bit}`               | `ANDB(bit)`              | `AND(C, bit)` or `AND(bit)`                   | 5, 6 |
| `ANL C, /{bit}`              | `ANDNB(bit)`             | `ANDB(~bit)` or `AND(C, ~bit)` or `AND(~bit)` | 5, 6 |
| `ORL C, {bit}`               | `ORB(bit)`               | `OR(C, bit)` or `OR(bit)`                     | 5, 6 |
| `ORL C, /{bit}`              | `ORNB(bit)`              | `ORB(~bit)` or `OR(C, bit)` or `OR(~bit)`     | 5, 6 |
| `MOV C, {bit}`               | `LDB(bit)`               |                                               |      |
| `MOV {bit}, C`               | `STB(bit)`               |                                               |      |
| `JC {rel}`                   | `JC(label)`              | `JB(C, label)`                                | 1    |
| `JNC {rel}`                  | `JNC(label)`             | `JNB(C, label)`                               | 1    |
| `JB {bit}, {rel}`            | `JB(bit, label)`         |                                               |      |
| `JNB {bit}, {rel}`           | `JNB(bit, label)`        |                                               |      |
| `JBC {bit}, {rel}`           | `JBC(bit, label)`        |                                               |      |
| **Control flow operations**  |                          |                                               |      |
| `CALL {addr}`                | `CALL(label)`            |                                               | 1, 2 |
| `ACALL {addr11}`             | `ACALL(label)`           |                                               | 1, 3 |
| `LCALL {addr16}`             | `LCALL(label)`           |                                               | 1    |
| `RET`                        | `RET()`                  |                                               |      |
| `RETI`                       | `RETI()`                 |                                               |      |
| `JMP {addr}`                 | `JMP(label)`             |                                               | 1, 2 |
| `AJMP {addr11}`              | `AJMP(label)`            |                                               | 1, 3 |
| `LJMP {addr16}`              | `LJMP(label)`            |                                               | 1    |
| `SJMP {rel}`                 | `SJMP(label)`            |                                               | 1    |
| `JMP @A + DPTR`              | `JMPA(A + DPTR)`         |                                               |      |
| `JZ {rel}`                   | `JZ(label)`              |                                               | 1    |
| `JNZ {rel}`                  | `JNZ(label)`             |                                               | 1    |
| `CJNE A, {dir}, {rel}`       | `CJNE(A, dir, label)`    |                                               | 1    |
| `CJNE A, #{imm}, {rel}`      | `CJNEI(A, imm, label)`   |                                               | 1    |
| `CJNE Rn, #{imm}, {rel}`     | `CJNEI(Rn, imm, label)`  | `CJNE(Rn, imm, label)`                        | 1    |
| `CJNE @Ri, #{imm}, {rel}`    | `CJNEAI(Ri, imm, label)` | `CJNEA(Ri, imm, label)`                       | 1    |
| `DJNZ Rn, {rel}`             | `DJNZ(Rn, label)`        |                                               | 1    |
| `DJNZ {dir}, {rel}`          | `DJNZ(dir, label)`       |                                               | 1    |
| **Not an operation**         |                          |                                               |      |
| `NOP`                        | `NOP()`                  |                                               |      |



Notes
-----

1. Jumps with literal addresses are discouraged in `yay` as they are error-prone
   and because `yay` does not specify in which order different blocks will be
   ordered.
2. These are pseudo instructions that are assembled into `S`-, `A`- or `LCALL`s
   or -`JMP`s.
3. `yay` does not guarantee the order of functions in the assembled program,
   hence implementing `ACALL` and `AJMP` correctly could be difficult.
4. The mnemonics that end in `A` are consistent with the other mnemonics where
   an `A` suffix denotes indirect access (e. g. `ANDA(A, Ri)` → “AND `A` with
   data *at* location `Ri`”). The forms without the ending `A` are more concise
   (there is no `STX` and `LDX` that is *not* indirect, hence the `A` is
   redundant).
5. Hmm... **TODO!**
6. The one-argument form would be distinguished by the type of the argument.
   Disadvantage: More implicit.
