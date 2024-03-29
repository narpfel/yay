import re
from functools import partial

from yay.helpers import (
    InvalidConfigError, WrongSignatureException, twos_complement,
    with_bind_program,
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


@with_bind_program
class Mnemonic:
    _SHORT_BIT_FORMAT = re.compile(r"(\w)(\d+)")

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

        self._opcode = None

        if auto:
            self.program.append(self)

    @property
    def size(self):
        return len(self.signature["opcode"])

    @property
    def opcode(self):
        if self._opcode is None:
            self._opcode = self.find_opcode()
        return self._opcode

    @property
    def position(self):
        return self.program.get_position(self)

    def find_matching_signature(self, args, kwargs):
        if kwargs:
            matcher = partial(self.matches_kwargs, kwargs)
        else:
            matcher = partial(self.matches_args, args)

        for signature in self.signatures:
            argument_format = signature["signature"]
            matches, alternatives_taken = matcher(argument_format)
            if matches:
                signature = dict(signature)
                signature["alternatives_taken"] = alternatives_taken
                signature["signature"] = [
                    alternatives_taken.get(name, name)
                    for name in signature["signature"]
                ]
                return signature

        raise WrongSignatureException(
            f"Cannot call {self.__class__.__name__} with this signature: "
            f"{args!r}, {kwargs!r}"
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

    def find_opcode(self):
        return bytes(
            twos_complement(
                self.process_byte(byte_format),
                8
            )
            for byte_format in self.signature["opcode"]
        )

    def process_byte(self, byte_format):
        if len(byte_format) == 1:
            # TODO: Should arguments unconditionally be converted to `int`?
            # Does this promote subtle bugs in production code?
            return int(self.try_match_byte(byte_format[0]))
        elif len(byte_format) == 8:
            result = 0
            for digit, bit_format in enumerate(reversed(byte_format)):
                result |= self.try_match_bit(bit_format) << digit
            return result
        else:
            raise InvalidConfigError(
                f"`byte_format` length must be either 1 or 8, not {len(byte_format)}"
            )

    def try_match_byte(self, byte_format):
        try:
            return int(byte_format)
        except ValueError:
            alternatives_taken = self.signature["alternatives_taken"]
            if byte_format in alternatives_taken:
                from_type = alternatives_taken[byte_format]
                return self.program.convert(
                    self,
                    from_type,
                    byte_format,
                    self._init_kwargs[from_type]
                )
            else:
                return self._init_kwargs[byte_format]

    def try_match_bit(self, bit_format):
        try:
            match = self._SHORT_BIT_FORMAT.match(bit_format)
        except TypeError:
            return int(bit_format)
        short = match.group(1)
        digit = int(match.group(2))
        typename = self.program.cpu["short_to_argname"][short]
        return get_bit(int(self.try_match_byte(typename)), digit)

    def __repr__(self):
        if hasattr(self, "_init_kwargs"):
            args = ", ".join(
                f"{name}={value}"
                for name, value in self._init_kwargs.items()
            )
        else:
            args = "?"
        return f"{self.__class__.__name__}({args})"


class Lit(Mnemonic):
    def __init__(self, byte, auto=True):
        if byte not in range(2 ** 8):
            raise WrongSignatureException(
                f"`byte` must be in range(256), not `{byte}`"
            )
        self.byte = byte
        self.signatures = [
            {
                "signature": [],
                "opcode": [[byte]]
            }
        ]
        super().__init__(auto=auto)
