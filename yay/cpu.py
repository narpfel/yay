from pathlib import Path

from yay.helpers import read_config, config_filename
from yay.mnemonics import make_mnemonics


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
