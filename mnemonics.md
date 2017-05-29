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

* The arrow operator `<-` is syntactic sugar for the `MOV` mnemonic.
  `x <- y` is always equivalent to `mov(x, y)`.
* `MOVC` has been renamed to `lpm` (load program memory). The accu does not
  have to be specified as an argument to this mnemonic.
* `MOVX` has been split into `ldx` (load external) and `stx` (store external).
  Like `lpm`, the accu is not explicitly specified as an argument.


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


| Mnemonic (with operands)     | `yay` equivalent           | `yay` alternative (under consideration) | Note |
|:-----------------------------|:---------------------------|:----------------------------------------|:-----|
| **Arithmetic operations**    |                            |                                         |      |
| ``ADD A, {dir}``             | `ADD(dir)`                 |                                         |      |
| ``ADD A, @Ri``               | `ADD(at(Ri))`              |                                         |      |
| ``ADD A, Rn``                | `ADD(Rn)`                  |                                         |      |
| ``ADD A, #{imm}``            | `ADD(imm)`                 |                                         |      |
| ``ADDC A, {dir}``            | `ADDC(dir)`                |                                         |      |
| ``ADDC A, @Ri``              | `ADDC(at(Ri))`             |                                         |      |
| ``ADDC A, Rn``               | `ADDC(Rn)`                 |                                         |      |
| ``ADDC A, #{imm}``           | `ADDC(imm)`                |                                         |      |
| ``SUBB A, {dir}``            | `SUBB(dir)`                |                                         |      |
| ``SUBB A, @Ri``              | `SUBB(at(Ri))`             |                                         |      |
| ``SUBB A, Rn``               | `SUBB(Rn)`                 |                                         |      |
| ``SUBB A, #{imm}``           | `SUBB(imm)`                |                                         |      |
| `INC A`                      | `INC()`                    |                                         |      |
| `INC {dir}`                  | `INC(dir)`                 |                                         |      |
| `INC @Ri`                    | `INC(at(Ri))`              |                                         |      |
| `INC Rn`                     | `INC(Rn)`                  |                                         |      |
| `INC DPTR`                   | `INC(DPTR)`                |                                         |      |
| `DEC A`                      | `DEC()`                    |                                         |      |
| `DEC {dir}`                  | `DEC(dir)`                 |                                         |      |
| `DEC @Ri`                    | `DEC(at(Ri))`              |                                         |      |
| `DEC Rn`                     | `DEC(Rn)`                  |                                         |      |
| `MUL AB`                     | `MUL()`                    |                                         |      |
| `DIV AB`                     | `DIV()`                    |                                         |      |
| `DA A`                       | `DA()`                     |                                         |      |
| **Logical operations**       |                            |                                         |      |
| `ANL A, {dir}`               | `AND(dir)`                 |                                         |      |
| `ANL A, @Ri`                 | `AND(at(Ri))`              |                                         |      |
| `ANL A, Rn`                  | `AND(Rn)`                  |                                         |      |
| `ANL A, #{imm}`              | `AND(imm)`                 |                                         |      |
| `ANL {dir}, A`               | `AND(dir, A)`              |                                         |      |
| `ANL {dir}, #{imm}`          | `AND(dir, imm)`            |                                         |      |
| `ORL A, {dir}`               | `OR(dir)`                  |                                         |      |
| `ORL A, @Ri`                 | `OR(at(Ri))`               |                                         |      |
| `ORL A, Rn`                  | `OR(Rn)`                   |                                         |      |
| `ORL A, #{imm}`              | `OR(imm)`                  |                                         |      |
| `ORL {dir}, A`               | `OR(dir, A)`               |                                         |      |
| `ORL {dir}, #{imm}`          | `OR(dir, imm)`             |                                         |      |
| `XRL A, {dir}`               | `XOR(dir)`                 |                                         |      |
| `XRL A, @Ri`                 | `XOR(at(Ri))`              |                                         |      |
| `XRL A, Rn`                  | `XOR(Rn)`                  |                                         |      |
| `XRL A, #{imm}`              | `XOR(imm)`                 |                                         |      |
| `XRL {dir}, A`               | `XOR(dir, A)`              |                                         |      |
| `XRL {dir}, #{imm}`          | `XOR(dir, imm)`            |                                         |      |
| `CLR A`                      | `CLR()`                    |                                         |      |
| `CPL A`                      | `CPL()`                    |                                         |      |
| `RL A`                       | `RL()`                     |                                         |      |
| `RLC A`                      | `RLC()`                    |                                         |      |
| `RR A`                       | `RR()`                     |                                         |      |
| `RRC A`                      | `RRC()`                    |                                         |      |
| `SWAP A`                     | `SWAP()`                   |                                         |      |
| **Data transfer operations** |                            |                                         |      |
| `MOV A, Rn`                  | `A <- Rn`                  |                                         |      |
| `MOV A, {dir}`               | `A <- dir`                 |                                         |      |
| `MOV A, @Ri`                 | `A <- at(Ri)`              |                                         |      |
| `MOV A, #{imm}`              | `A <- imm`                 |                                         |      |
| `MOV Rn, A`                  | `Rn <- A`                  |                                         |      |
| `MOV Rn, {dir}`              | `Rn <- dir`                |                                         |      |
| `MOV Rn, #{imm}`             | `Rn <- imm`                |                                         |      |
| `MOV {dir}, A`               | `dir <- A`                 |                                         |      |
| `MOV {dir}, Rn`              | `dir <- Rn`                |                                         |      |
| `MOV {dir}, {dir}`           | `dir <- dir`               |                                         |      |
| `MOV {dir}, @Ri`             | `dir <- at(Ri)`            |                                         |      |
| `MOV {dir}, #{imm}`          | `dir <- imm`               |                                         |      |
| `MOV @Ri, A`                 | `at(Ri) <- A`              |                                         |      |
| `MOV @Ri, {dir}`             | `at(Ri) <- dir`            |                                         |      |
| `MOV @Ri, #{imm}`            | `at(Ri) <- imm`            |                                         |      |
| `MOV DPTR, {addr16}`         | `DPTR <- addr16`           |                                         |      |
| `MOVC A, @A+DPTR`            | `LPM(at(A + DPTR))`        |                                         |      |
| `MOVC A, @A+PC`              | `LPM(at(A + PC))`          |                                         |      |
| `MOVX A, @Ri`                | `LDX(at(Ri))`              |                                         |      |
| `MOVX A, @DPTR`              | `LDX(at(DPTR))`            |                                         |      |
| `MOVX @Ri, A`                | `STX(at(Ri))`              |                                         |      |
| `MOVX @DPTR, A`              | `STX(at(DPTR))`            |                                         |      |
| `PUSH {dir}`                 | `PUSH(dir)`                |                                         |      |
| `POP {dir}`                  | `POP(dir)`                 |                                         |      |
| `XCH A, {dir}`               | `XCH(A, dir)`              |                                         |      |
| `XCH A, @Ri`                 | `XCH(A, at(Ri))`           |                                         |      |
| `XCH A, Rn`                  | `XCH(A, Rn)`               |                                         |      |
| `XCHD A, @Ri`                | `XCHD(A, at(Ri))`          |                                         |      |
| **Boolean operations**       |                            |                                         |      |
| `CLR C`                      | `CLR(C)`                   |                                         |      |
| `CLR {bit}`                  | `CLR(bit)`                 |                                         |      |
| `SETB C`                     | `SET(C)`                   |                                         |      |
| `SETB {bit}`                 | `SET(bit)`                 |                                         |      |
| `CPL C`                      | `CPL(C)`                   |                                         |      |
| `CPL {bit}`                  | `CPL(bit)`                 |                                         |      |
| `ANL C, {bit}`               | `AND(bit)`                 |                                         |      |
| `ANL C, /{bit}`              | `AND(~bit)`                |                                         |      |
| `ORL C, {bit}`               | `OR(bit)`                  |                                         |      |
| `ORL C, /{bit}`              | `OR(~bit)`                 |                                         |      |
| `MOV C, {bit}`               | `C <- bit`                 |                                         |      |
| `MOV {bit}, C`               | `bit <- C`                 |                                         |      |
| `JC {rel}`                   | `JC(label)`                | `JB(C, label)`                          | 1    |
| `JNC {rel}`                  | `JNC(label)`               | `JNB(C, label)`                         | 1    |
| `JB {bit}, {rel}`            | `JB(bit, label)`           |                                         |      |
| `JNB {bit}, {rel}`           | `JNB(bit, label)`          |                                         |      |
| `JBC {bit}, {rel}`           | `JBC(bit, label)`          |                                         |      |
| **Control flow operations**  |                            |                                         |      |
| `CALL {addr}`                | `CALL(label)`              |                                         | 1, 2 |
| `ACALL {addr11}`             | `ACALL(label)`             |                                         | 1, 3 |
| `LCALL {addr16}`             | `LCALL(label)`             |                                         | 1    |
| `RET`                        | `RET()`                    |                                         |      |
| `RETI`                       | `RETI()`                   |                                         |      |
| `JMP {addr}`                 | `JMP(label)`               |                                         | 1, 2 |
| `AJMP {addr11}`              | `AJMP(label)`              |                                         | 1, 3 |
| `LJMP {addr16}`              | `LJMP(label)`              |                                         | 1    |
| `SJMP {rel}`                 | `SJMP(label)`              |                                         | 1    |
| `JMP @A + DPTR`              | `JMP(at(A + DPTR))`        |                                         |      |
| `JZ {rel}`                   | `JZ(label)`                |                                         | 1    |
| `JNZ {rel}`                  | `JNZ(label)`               |                                         | 1    |
| `CJNE A, {dir}, {rel}`       | `CJNE(A, dir, label)`      |                                         | 1    |
| `CJNE A, #{imm}, {rel}`      | `CJNE(A, imm, label)`      |                                         | 1    |
| `CJNE Rn, #{imm}, {rel}`     | `CJNE(Rn, imm, label)`     |                                         | 1    |
| `CJNE @Ri, #{imm}, {rel}`    | `CJNE(at(Ri), imm, label)` |                                         | 1    |
| `DJNZ Rn, {rel}`             | `DJNZ(Rn, label)`          |                                         | 1    |
| `DJNZ {dir}, {rel}`          | `DJNZ(dir, label)`         |                                         | 1    |
| **Not an operation**         |                            |                                         |      |
| `NOP`                        | `NOP()`                    |                                         |      |



Notes
-----

1. Jumps with literal addresses are discouraged in `yay` as they are error-prone
   and because `yay` does not specify in which order different blocks will be
   ordered.
2. These are pseudo instructions that are assembled into `S`-, `A`- or `LCALL`s
   or -`JMP`s. They will likely be be implemented as macros. Furthermore,
   instruction length will have to be known on first pass (when labels have been
   implemented) so that correct relative addresses can be computed on the
   second pass.
3. `yay` does not guarantee the order of functions in the assembled program,
   hence implementing `ACALL` and `AJMP` correctly could be difficult.
