from yay.helpers import read_config, config_filename, InvalidRegisterError
from yay.mnemonics import make_mnemonic


# TODO: Move to a better place (maybe a module that holds all mcs51 specific
# stuff).
def at(register):
    try:
        if register.can_indirect:
            return register.as_indirect
        else:
            raise InvalidRegisterError(
                "{} can not be used as indirect.".format(register)
            )
    except AttributeError as err:
        raise TypeError("Not a register: {!r}.".format(register)) from err


class AT89S8253:
    _config = read_config(
        config_filename("cpu_configurations/AT89S8253.yml")
    )
    signature_contents = _config["signature_contents"]
    registers = _config["registers"]

    mnemonics = {}
    for name, signatures in _config["mnemonics"].items():
        mnemonics[name] = make_mnemonic(name, signatures, signature_contents)
    del name
    del signatures

    all = dict(mnemonics)
    all.update(_config["registers"])
    all.update(_config["additional_names"])
