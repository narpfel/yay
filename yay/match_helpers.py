from yay.registers import Accumulator


def is_register(candidate):
    return hasattr(candidate, "number") and not is_indirect(candidate)


def is_direct(candidate):
    return candidate in range(256)


def is_indirect(candidate):
    return (
        hasattr(candidate, "number")
        and hasattr(candidate, "indirect")
        and candidate.indirect
    )


def is_immediate(candidate):
    return candidate in range(-128, 256)


def is_addr11(candidate):
    return candidate in range(2 ** 11)


def is_accu(candidate):
    return isinstance(candidate, Accumulator)
