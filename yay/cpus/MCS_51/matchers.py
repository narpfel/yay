from yay.cpus.MCS_51 import (
    Accumulator, DPTR, IndirectDptr, DptrOffset, PcOffset, Carry, Label,
)


def is_direct(candidate):
    return hasattr(candidate, "byte_addr") and candidate.byte_addr in range(256)


is_direct_dest = is_direct


def is_register(candidate):
    return hasattr(candidate, "number")


def is_indirect(candidate):
    return hasattr(candidate, "indirect_number")


def is_immediate(candidate):
    return candidate in range(-128, 256)


def is_immediate16(candidate):
    return candidate in range(2 ** 16)


def is_label(candidate):
    return isinstance(candidate, (str, Label))


def is_relative(candidate, from_alternative=False):
    return from_alternative and candidate in range(-2 ** 7, 2 ** 7 - 1)


def is_addr11(candidate, from_alternative=False):
    return from_alternative and candidate in range(2 ** 11)


def is_addr16(candidate, from_alternative=False):
    return candidate in range(2 ** 16)


def is_accu(candidate):
    return isinstance(candidate, Accumulator)


def is_dptr(candidate):
    return isinstance(candidate, DPTR)


def is_indirect_dptr(candidate):
    return isinstance(candidate, IndirectDptr)


def is_dptr_offset(candidate):
    return isinstance(candidate, DptrOffset)


def is_pc_offset(candidate):
    return isinstance(candidate, PcOffset)


def is_carry(candidate):
    return isinstance(candidate, Carry)


def is_bit(candidate):
    return hasattr(candidate, "bit_addr") and candidate.bit_addr in range(256)


def is_not_bit(candidate):
    return hasattr(candidate, "not_bit_addr") and candidate.not_bit_addr in range(256)


def is_pushpop_register(candidate, from_alternative=False):
    return from_alternative and candidate in range(256)
