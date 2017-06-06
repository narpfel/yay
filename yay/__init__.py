import sys

import yay_ast as ast

from yay.program import Program, sub, macro, block_macro, Mod
from yay.helpers import (
    InvalidRegisterError, InvalidConfigError, WrongSignatureException
)
from yay.importer import YayFinder


__all__ = [
    "Program", "sub", "macro", "block_macro", "Mod", "InvalidRegisterError",
    "InvalidConfigError", "WrongSignatureException",
]


sys.meta_path.insert(0, YayFinder())
