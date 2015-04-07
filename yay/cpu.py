import os.path
from pathlib import Path
from importlib import import_module

from yay.helpers import read_config, config_filename
from yay.mnemonics import make_mnemonics


def _insert_default_from(import_spec, default_from):
    if "from" not in import_spec:
        import_spec["from"] = default_from


def _import_object(from_, name):
    return getattr(import_module(from_), name)


def _read_import_spec(import_spec, default_from):
    try:
        import_spec["import"]
    except (KeyError, TypeError):
        # Not a valid `import_spec`, ignoring.
        return import_spec
    _insert_default_from(import_spec, default_from)
    imported = _import_object(import_spec["from"], import_spec["import"])
    if "call" in import_spec:
        return imported(*import_spec["call"])
    else:
        return imported


def _replace_imports(section, default_from):
    for name, import_spec in section.items():
        section[name] = _read_import_spec(import_spec, default_from)


def read_cpu_config(config_name):
    config = read_config(config_name)

    for name, default in config.pop("importing", {}).items():
        _replace_imports(config[name], default)

    return config


def get_cpu_definition(cpu_name):
    if isinstance(cpu_name, Path) or os.path.isabs(cpu_name):
        return str(cpu_name)
    else:
        return config_filename("cpu_configurations/{}.yml".format(cpu_name))


def make_cpu(cpu_name):
    config = read_cpu_config(get_cpu_definition(cpu_name))
    config["mnemonics"] = make_mnemonics(config)
    return config
