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


`LD` mnemonic
-------------

When writing a macro, it is useful to accept direct as well as register and
indirect addresses as arguments. If this is the case, `LDA`, `LDD` and `LDI`
cannot be used anymore because they encode their argument type in their names.
Introducing a polymorphic mnmonic `LD` will solve this problem. It should
be made clear that in situations when the argument type is known at write
time, for clarity reasons the specialized `LDA`, `LDD` and `LDI` are preferred.


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
