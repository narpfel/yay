from yay.helpers import read_config
from yay.mnemonics import make_mnemonic
import yay.registers


class AT89S8253:
    _config = read_config("cpu_configurations/AT89S8253.yml")
    signature_contents = _config["signature_contents"]

    mnemonics = {}
    for name, signatures in _config["mnemonics"].items():
        mnemonics[name] = make_mnemonic(name, signatures, signature_contents)
    del name
    del signatures

    registers = yay.registers.AT89S8253.registers

    all = dict(mnemonics)
    all.update(registers)
    all["at"] = yay.registers.at
