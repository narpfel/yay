def addr16_from_label(mnemonic, label):
    return mnemonic.program.labels[label]


def relative_from_addr16(mnemonic, addr16):
    return addr16 - (mnemonic.position + mnemonic.size)


def relative_from_label(mnemonic, label):
    return relative_from_addr16(mnemonic, addr16_from_label(mnemonic, label))


def addr11_from_addr16(mnemonic, addr16):
    jump_start = mnemonic.position + mnemonic.size
    if jump_start >> 11 != addr16 >> 11:
        raise ValueError(
            f"Can’t reach address {addr16} from {jump_start} "
            "(must be in the same 2k block)"
        )
    return addr16 & 2 ** 11 - 1


def addr11_from_label(mnemonic, label):
    return addr11_from_addr16(mnemonic, addr16_from_label(mnemonic, label))


def pushpop_register_from_accu(mnemonic, accu):
    return accu.direct_address


def pushpop_register_from_register(mnemonic, register):
    return register.direct_address


def pushpop_register_from_direct(mnemonic, direct):
    return direct.byte_addr
