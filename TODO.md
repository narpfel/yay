TODO
====


Target handling in mnemonics
----------------------------

Calling a mnemonic should let the mnemonic append it`self` to its `target`.
This way, the `Program` has kind of a syntax tree that it can (post-)process
later. It should be possible for `with`-blocks to alter the mnemonics’ targets
in order to capture the mnemonics in their blocks to customize program
behaviour. For that, the mnemonics should receive a callable (e. g. a method
of `Program`) that returns the actual `target` so that the target itself can
be easily replaced for all mnemonics.

To assist [TODO: ???]


CPU definitions
---------------

A CPU definition should be completely contained in one yaml config file.
There should be a function `read_cpu_definition` (?) that takes a CPU name and
returns a dictionary representing the specified CPU. It should be possible to
use this return value as the `cpu` argument for `Program` subclasses.


Config files in data directories
--------------------------------

Move all config files to `yay/configurations` and load them via `pkg_resources`.
Implement function `yay.get_cpu` that either takes a predefined CPU name and
loads that CPU definition via `pkg_resources` or a `pathlib.Path` instance
and loads the config file from that path. Maybe for predefined CPUs there
should be an importable name in `yay.cpu`.


`LD` mnemonic
-------------

When writing a macro, it is useful to accept direct as well as register and
indirect addresses as arguments. If this is the case, `LDA`, `LDD` and `LDI`
cannot be used anymore because they encode their argument type in their names.
Introducing a polymorphic mnmonic `LD` will solve this problem. It should
be made clear that in situations when the argument type is known at write
time, for clarity reasons the specialized `LDA`, `LDD` and `LDI` are preferred.


Isolation
---------

All tests `tests/test_isolation.py` should pass. Solution: On instantiation of
`_Program`, `_Program.__init__()` should use the configuration dict to create
a new set of CPU specific objects.

For that, the `cpu` keyword argument should accept a string that is interpreted
as the config file location. See “Config files in data directories”.


`immediate` function
--------------------

For macros, it could sometimes be wanted to pass an immediate where
a direct, register or indirect was expected. Therefore it should be possible
to override mnemonic signature selection with the `immediate`-Function.
To implement this, YAML references could be used. On the other hand, it may be
possible to implement an own reference mechanism, but this seems like
reinventing the wheel. Alternatively, mnemonics that have both a form *with*
and *without* a trailing `I` could be automagically converted to support
`immediate`. Disadvantage: More implicit and may not be always wanted.
Furthermore, for this to work the mnemonic creation process would have to
know the names and signatures of *all* mnemonics.

> Explicit is better than implicit.

The problem with references is that directs and immediates are (by design) not
distinguishable from each other (as they are `int`s), so a mnemonic cannot have
both an `immediate` and a `direct` as its argument. This is solved by
adding a `forced: true` key to the signature dict. This will force the
opcode selection mechanism to use the `is_forced_immediate` matcher instead
of the `is_immediate` matcher.

Example implementation:

```yaml
mnemonics:
    ADDI:
        - &ADDI
          signature: ["immediate"]
          opcode:
              - [0b0010_0100]
              - ["immediate"]
    ADD:
        - signature: ["direct"]
          opcode:
              - [0b0010_0101]
              - ["direct"]
        - signature: ["register"]
          opcode:
              - [0, 0, 1, 0, 1, "r2", "r1", "r0"]
        - signature: ["indirect"]
          opcode:
              - [0, 0, 1, 0, 0, 1, 1, "i0"]
        - <<: *ADDI
          forced: true
```


Config file inheritance
-----------------------

It should be possible to inherit from another config file (e. g. `AT89S8253`
could inherit from `MC51`) via the `inherit_from` key:

```yaml
inherit_from: "MC51"
mnemonics:
    ...
```

If the value of `inherit_from` is relative (according to `os.path.isabs`), it is
taken as a default config file (located at `yay/cpu_configurations`). Otherwise,
the file at the corresponding absolute path is used as a base YAML file.

Inheritance will be modeled by a simple recursive merge of the two configuration
dictionaries.
