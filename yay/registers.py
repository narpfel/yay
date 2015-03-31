class Accumulator:
    pass


class Register:
    def __init__(self, number, can_indirect=False):
        self.number = number
        self.can_indirect = can_indirect
        if can_indirect:
            self.as_indirect = IndirectRegister(number)
        else:
            self.as_indirect = None

    def __int__(self):
        return self.number

    def __str__(self):
        return "R{}".format(self.number)

    def __repr__(self):
        return "R{}()".format(self.number)


class IndirectRegister(Register):
    def __init__(self, number, can_indirect=True):
        super().__init__(number, False)
        self.can_indirect = True
        self.as_indirect = self
        self.indirect = True

    def __str__(self):
        return "IR{}".format(self.number)

    def __repr__(self):
        return "IR{}()".format(self.number)
