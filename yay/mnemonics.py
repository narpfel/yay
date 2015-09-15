from functools import partial
import re

from yay.helpers import (
    InvalidConfigError, WrongSignatureException, twos_complement
)


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


def make_mnemonic(name, signatures):
    return type(
        name,
        (Mnemonic, ),
        dict(signatures=signatures)
    )


def make_mnemonics(config):
    return {
        name: make_mnemonic(name, signatures)
        for name, signatures in config["mnemonics"].items()
    }


class Mnemonic:
    def __init__(self, *args, **kwargs):
        auto = kwargs.pop("auto", True)

        self._init_args = args
        self._init_kwargs = kwargs

        if args and kwargs:
            raise WrongSignatureException(
                "Mixing of positional and keyword arguments is not allowed."
            )

        self.signature, self.opcode = self.find_opcode(args, kwargs)

        if auto:
            self.program.append(self)

    @classmethod
    def bind_program(cls, program):
        return type(cls.__name__, (cls, ), dict(program=program))

    @property
    def size(self):
        return len(self.opcode)

    def find_opcode(self, args, kwargs):
        for signature in self.signatures:
            opcode_format = signature["opcode"]
            argument_format = signature["signature"]

            if argument_format and self.matches_kwargs(kwargs, argument_format):
                return signature, self.opcode_from_kwargs(
                    opcode_format, kwargs
                )
            elif self.matches_args(args, argument_format):
                return signature, self.opcode_from_args(
                    opcode_format, argument_format, args
                )
        raise WrongSignatureException(
            "Cannot call {} with this signature: {!r}, {!r}".format(
                self.__class__.__name__, args, kwargs
            )
        )

    def matches_args(self, args, argument_format):
        return len(args) == len(argument_format) and all(
            getattr(
                self.program.cpu["matchers"]["matchers"],
                "is_{}".format(name)
            )(argument)
            for name, argument in zip(argument_format, args)
        )

    def matches_kwargs(self, kwargs, argument_format):
        return set(kwargs) == set(argument_format) and self.matches_args(
            [kwargs[argname] for argname in argument_format],
            argument_format,
        )

    def opcode_from_args(self, opcode_format, argument_format, args):
        return self.opcode_from_kwargs(
            opcode_format,
            dict(zip(argument_format, args)),
        )

    def opcode_from_kwargs(self, opcode_format, kwargs):
        return bytes(
            twos_complement(
                self.process_byte(byte_format, kwargs),
                8
            )
            for byte_format in opcode_format
        )

    def process_byte(self, byte_format, kwargs):
        try:
            if len(byte_format) == 1:
                # TODO: Should arguments unconditionally be converted to `int`?
                # Does this promote subtle bugs in production code?
                return int(try_match_byte(byte_format[0], kwargs))
            elif len(byte_format) == 8:
                result = 0
                for digit, bit_format in enumerate(reversed(byte_format)):
                    result |= try_match_bit(
                        bit_format, self.program.cpu["short_to_argname"], kwargs
                    ) << digit
                return result
            else:
                raise ValueError("`byte_format` length must be either 1 or 8.")
        except ValueError as err:
            raise InvalidConfigError(
                "Invalid configuration: {!r}".format(byte_format)
            ) from err

    def __repr__(self):
        return "{name}({args})".format(
            name=self.__class__.__name__,
            args=", ".join(
                "{}={}".format(name, value)
                for name, value in (
                    zip(self.signature["signature"], self._init_args)
                    if self._init_args
                    else self._init_kwargs.items()
                )
            )
        )
