from functools import partial
import re

from yay import match_helpers
from yay.helpers import (
    reverse_dict, InvalidConfigError, WrongSignatureException, twos_complement
)


def matches_args(args, argument_format):
    return len(args) == len(argument_format) and all(
        getattr(
            match_helpers,
            "is_{}".format(name)
        )(argument)
        for name, argument in zip(argument_format, args)
    )


def matches_kwargs(kwargs, argument_format):
    return set(kwargs) == set(argument_format) and matches_args(
        [kwargs[argname] for argname in argument_format],
        argument_format
    )


def opcode_from_args(opcode_format, argument_format, args, signature_contents):
    return opcode_from_kwargs(
        opcode_format,
        dict(zip(argument_format, args)),
        signature_contents
    )


def opcode_from_kwargs(opcode_format, kwargs, signature_contents):
    return bytes(
        twos_complement(
            process_byte(byte_format, kwargs, signature_contents),
            8
        )
        for byte_format in opcode_format
    )


def process_byte(byte_format, kwargs, signature_contents):
    try:
        if len(byte_format) == 1:
            # TODO: Should arguments unconditionally be converted to `int`?
            # Does this promote subtle bugs in production code?
            return int(try_match_byte(byte_format[0], kwargs))
        elif len(byte_format) == 8:
            short_to_argname = reverse_dict({
                # TODO: Better name for `value`.
                argname: value["short"]
                for argname, value in signature_contents.items()
                if value["short"] is not None
            })
            result = 0
            for digit, bit_format in enumerate(reversed(byte_format)):
                result |= try_match_bit(
                    bit_format, short_to_argname, kwargs
                ) << digit
            return result
        else:
            raise ValueError("`byte_format` length must be either 1 or 8.")
    except ValueError as err:
        raise InvalidConfigError(
            "Invalid configuration: {!r}".format(byte_format)
        ) from err


def try_match_bit(bit_format, short_to_argname, kwargs):
    try:
        match = re.match(r"(\w)(\d+)", bit_format)
    except TypeError:
        return int(bit_format)
    else:
        short = match.group(1)
        digit = int(match.group(2))
        return get_bit(int(kwargs[short_to_argname[short]]), digit)


def try_match_byte(byte_format, kwargs):
    try:
        return kwargs[byte_format]
    except KeyError:
        return byte_format


def get_bit(number, bit):
    return (number >> bit) & 1


def make_mnemonic(name, signatures, signature_contents):
    def __init__(self, *args, **kwargs):
        try:
            super_args = {"auto": kwargs.pop("auto")}
        except KeyError:
            super_args = {}
        Mnemonic.__init__(self, **super_args)
        self._signature_contents = signature_contents

        if args and kwargs:
            raise WrongSignatureException(
                "Mixing of positional and keyword arguments is not allowed."
            )

        # TODO: Refactor this `for` loop into a method/function that returns
        # `(init_args, signature, opcode)`.
        for signature in signatures:
            self.init_args = kwargs
            self.signature = signature
            opcode_format = signature["opcode"]
            argument_format = signature["signature"]

            if argument_format and matches_kwargs(kwargs, argument_format):
                self.opcode = opcode_from_kwargs(
                    opcode_format, kwargs, signature_contents
                )
                break
            elif matches_args(args, argument_format):
                self.opcode = opcode_from_args(
                    opcode_format, argument_format, args, signature_contents
                )
                break
        else:
            raise WrongSignatureException(
                "Cannot call {} with this signature: {!r}, {!r}".format(
                    self.__class__.__name__, args, kwargs
                )
            )

    return type(name, (Mnemonic, ), {"__init__": __init__})


def make_mnemonics(config):
    return {
        name: make_mnemonic(name, signatures, config["signature_contents"])
        for name, signatures in config["mnemonics"].items()
    }


class Mnemonic:
    def __init__(self, auto=True):
        if auto:
            self.program.append(self)

    @classmethod
    def bind_program(cls, program):
        return type(cls.__name__, (cls, ), dict(program=program))

    @property
    def size(self):
        return len(self.opcode)

    def __repr__(self):
        return "{name}({args})".format(
            name=self.__class__.__name__,
            args=", ".join(
                "{}={}".format(name, value)
                for name, value in zip(self.signature, self.init_args)
            )
        )
