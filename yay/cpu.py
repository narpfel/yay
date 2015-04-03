from pathlib import Path

from yay.helpers import read_config, config_filename, InvalidRegisterError
from yay.mnemonics import make_mnemonics


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


def get_cpu_definition(cpu_name):
    if isinstance(cpu_name, Path):
        return read_config(str(cpu_name))
    else:
        return read_config(
            config_filename("cpu_configurations/{}.yml".format(cpu_name))
        )


def make_cpu(cpu_name):
    config = get_cpu_definition(cpu_name)
    config["mnemonics"] = make_mnemonics(config)
    return config
