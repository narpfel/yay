from functools import partial
import re

from yay.helpers import (
    InvalidConfigError, WrongSignatureException, twos_complement
)


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
    program = None
    signatures = None

    def __init__(self, *args, **kwargs):
        auto = kwargs.pop("auto", True)

        if args and kwargs:
            raise WrongSignatureException(
                "Mixing of positional and keyword arguments is not allowed."
            )

        self.signature = self.find_matching_signature(args, kwargs)

        if kwargs:
            self._init_kwargs = kwargs
        else:
            self._init_kwargs = self.kwargs_from_args(
                self.signature["signature"],
                args
            )

        self.opcode = self.opcode_from_kwargs(
            self.signature,
            self._init_kwargs
        )

        if auto:
            self.program.append(self)

    @classmethod
    def bind_program(cls, program):
        return type(cls.__name__, (cls, ), dict(program=program))

    @property
    def size(self):
        return len(self.signature["opcode"])

    def find_matching_signature(self, args, kwargs):
        if kwargs:
            matcher = partial(self.matches_kwargs, kwargs)
        else:
            matcher = partial(self.matches_args, args)

        for signature in self.signatures:
            argument_format = signature["signature"]
            matches, alternatives_taken = matcher(argument_format)
            if matches:
                actual_signature = dict(signature)
                actual_signature["alternatives_taken"] = alternatives_taken
                actual_signature["signature"] = [
                    alternatives_taken.get(name, name)
                    for name in actual_signature["signature"]
                ]
                return actual_signature

        raise WrongSignatureException(
            "Cannot call {} with this signature: {!r}, {!r}".format(
                self.__class__.__name__, args, kwargs
            )
        )

    def matches_args(self, args, argument_format):
        if len(args) != len(argument_format):
            return False, {}

        alternatives_taken = {}
        for name, argument in zip(argument_format, args):
            has_matched, matched_type = self.program.matches(name, argument)
            if not has_matched:
                return False, {}
            if matched_type != name:
                alternatives_taken[name] = matched_type
        return True, alternatives_taken

    def matches_kwargs(self, kwargs, argument_format):
        if not argument_format or set(kwargs) != set(argument_format):
            return False, {}
        return self.matches_args(
            [kwargs[argname] for argname in argument_format],
            argument_format,
        )

    @staticmethod
    def kwargs_from_args(argument_format, args):
        return dict(zip(argument_format, args))

    def opcode_from_kwargs(self, signature, kwargs):
        return bytes(
            twos_complement(
                self.process_byte(byte_format, kwargs, signature),
                8
            )
            for byte_format in signature["opcode"]
        )

    def process_byte(self, byte_format, kwargs, signature):
        try:
            if len(byte_format) == 1:
                # TODO: Should arguments unconditionally be converted to `int`?
                # Does this promote subtle bugs in production code?
                return int(
                    self.try_match_byte(byte_format[0], kwargs, signature)
                )
            elif len(byte_format) == 8:
                result = 0
                for digit, bit_format in enumerate(reversed(byte_format)):
                    result |= self.try_match_bit(
                        bit_format,
                        self.program.cpu["short_to_argname"],
                        kwargs,
                        signature
                    ) << digit
                return result
            else:
                raise ValueError("`byte_format` length must be either 1 or 8.")
        except ValueError as err:
            raise InvalidConfigError(
                "Invalid configuration: {!r}".format(byte_format)
            ) from err

    def try_match_byte(self, byte_format, kwargs, signature):
        try:
            return int(byte_format)
        except ValueError:
            if byte_format in signature["alternatives_taken"]:
                return self.program.convert(
                    self,
                    byte_format,
                    signature["alternatives_taken"][byte_format],
                    kwargs[byte_format]
                )
            else:
                return kwargs[byte_format]

    def try_match_bit(self, bit_format, short_to_argname, kwargs, signature):
        try:
            match = re.match(r"(\w)(\d+)", bit_format)
        except TypeError:
            return int(bit_format)
        else:
            short = match.group(1)
            digit = int(match.group(2))
            typename = short_to_argname[short]
            if typename not in kwargs:
                type_to_alternative = signature["alternatives_taken"]
                from_type = type_to_alternative[typename]
                value = self.program.convert(
                    self,
                    from_type,
                    typename,
                    kwargs[from_type]
                )
            else:
                value = kwargs[typename]
            return get_bit(int(value), digit)

    def __repr__(self):
        return "{name}({args})".format(
            name=self.__class__.__name__,
            args=", ".join(
                "{}={}".format(name, value)
                for name, value in self._init_kwargs.items()
            )
            if hasattr(self, "_init_kwargs")
            else "?"
        )
