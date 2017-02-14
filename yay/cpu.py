import os.path
from pathlib import Path
from importlib import import_module

from yay.helpers import (
    read_config, config_filename, recursive_merge, reverse_dict
)
from yay.mnemonic import make_mnemonics, Lit


def _import_object(from_, name):
    return getattr(import_module(from_), name)


def _call_one(obj, name, args, with_key):
    if with_key:
        args = [name] + args
    return obj(*args)


def _call_many(obj, call_spec, with_key):
    return {
        name: _call_one(obj, name, args, with_key)
        for name, args in call_spec.items()
    }


def _read_import_spec(import_spec, default_from):
    try:
        name = import_spec["import"]
    except (KeyError, TypeError):
        # Not a valid `import_spec`, ignoring.
        return import_spec
    from_ = import_spec.get("from", default_from)
    imported = _import_object(from_, name)
    if "call" in import_spec:
        return imported(*import_spec["call"])
    else:
        return imported


def _replace_call_many_import(import_spec, default_from):
    try:
        name = import_spec["import"]
    except (KeyError, TypeError):
        # Not a valid `import_spec`, ignoring.
        return
    from_ = import_spec.get("from", default_from)
    imported = _import_object(from_, name)
    replacement = _call_many(
        imported,
        import_spec["call_many"],
        import_spec.get("with_key", False)
    )
    import_spec.clear()
    import_spec.update(replacement)


def _replace_imports(section, default_from):
    if "call_many" in section:
        _replace_call_many_import(section, default_from)
    else:
        for name, import_spec in section.items():
            section[name] = _read_import_spec(import_spec, default_from)


def short_to_argname(signature_contents):
    return reverse_dict({
        argname: argspec["short"]
        for argname, argspec in signature_contents.items()
        if argspec["short"] is not None
    })


def read_cpu_config(config_name):
    config = read_config(config_name)

    if "inherit_from" in config:
        config = recursive_merge(
            read_cpu_config(get_cpu_definition(config["inherit_from"])),
            config
        )

    for name, default in config.pop("importing", {}).items():
        _replace_imports(config[name], default)

    if "signature_contents" in config:
        config["short_to_argname"] = short_to_argname(config["signature_contents"])

    return config


def get_cpu_definition(cpu_name):
    if isinstance(cpu_name, Path) or os.path.isabs(cpu_name):
        return str(cpu_name)
    else:
        return config_filename("cpu_configurations/{}.yml".format(cpu_name))


def make_cpu(cpu_name):
    config = read_cpu_config(get_cpu_definition(cpu_name))
    config["mnemonics"] = make_mnemonics(config)
    config["mnemonics"]["Lit"] = Lit
    return config
