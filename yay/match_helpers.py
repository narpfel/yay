# TODO: Should this be moved to `yay.cpu.AT89S8253`?
# If so, mnemonics would have to know where to retrieve their `match_helpers`.
# This could be done via their config file.
# If not, *all* `match_helpers` fromm all cpu families would go here and name
# collisions would be possible.
# Preference: Yes.

from yay.cpus.AT89S8253 import Accumulator


def is_register(candidate):
    return hasattr(candidate, "number")


def is_direct(candidate):
    return candidate in range(256)


def is_indirect(candidate):
    return hasattr(candidate, "indirect_number")


def is_immediate(candidate):
    return candidate in range(-128, 256)


def is_forced_immediate(candidate):
    return hasattr(candidate, "immediate") and is_immediate(candidate.immediate)


def is_addr11(candidate):
    return candidate in range(2 ** 11)


def is_accu(candidate):
    return isinstance(candidate, Accumulator)
