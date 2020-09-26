from abc import ABC, abstractmethod, ABCMeta
import re
from typing import Type

from util.exception import ALEDException
from .exc import InvalidValue

IS_SIGNED_INT = re.compile(r"-?\d+")

class AbcConfigurerType(ABC, metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, inp=""):
        self.value = ...
        raise ALEDException(f"No constructor defined for {self.__class__.__name__}")

    @abstractmethod
    def __str__(self):
        return "<Representation not implemented>"

    def __repr__(self):
        return f"ConfigType({self.__class__.__name__}): {self.value if hasattr(self, 'value') else '<Not Define>'}"

    @property
    def type(self) -> str:
        return self.__class__.__name__

    @staticmethod
    @abstractmethod
    def is_valid(inp: str) -> bool:
        return False

    def to_json(self):
        return self.value

    def set_from_json(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other.value

class String(AbcConfigurerType):
    def __init__(self, inp=""):
        self.value = inp   # type: str

    def __str__(self):
        return self.value

    @staticmethod
    def is_valid(inp: str):
        return True

    def to_json(self) -> str:
        return self.value

class Int(AbcConfigurerType):
    def __init__(self, inp=0):
        self.value = int(inp)

    def __str__(self):
        return str(self.value)

    @staticmethod
    def is_valid(inp: str) -> bool:
        return inp.isdigit()

    def to_json(self) -> int:
        return self.value

class SignedInt(AbcConfigurerType):
    def __init__(self, inp=0):
        self.value = int(inp)

    def __str__(self):
        return str(self.value)

    @staticmethod
    def is_valid(inp: str) -> bool:
        return bool(IS_SIGNED_INT.match(inp))

    def to_json(self) -> int:
        return self.value

class Bool(AbcConfigurerType):
    def __init__(self, inp="False"):
        self.value = True if inp.lower() in ["1", "true"] else False

    def __str__(self):
        return str(self.value)

    @staticmethod
    def is_valid(inp: str) -> bool:
        return inp.lower() in ["0", "1", "false", "true"]

    def to_json(self) -> bool:
        return self.value

class DiscordUser(Int):
    def __str__(self):
        return f"<@{self.value}>"

class DiscordChannel(Int):
    def __str__(self):
        return f"<#{self.value}>"

class DiscordRole(Int):
    def __str__(self):
        return f"<@&{self.value}>"

class List(AbcConfigurerType):
    def __init__(self, *_, subtype: Type[AbcConfigurerType]):
        self.value = []
        self.subtype = subtype

    def __str__(self):
        return ', '.join([str(i) for i in self.value])

    @staticmethod
    def is_valid(inp: str):
        raise ALEDException("is_valid method from ConfigurerType.List should not be called")

    def to_json(self) -> list:
        return [i.to_json() for i in self.value]

    def set_from_json(self, value):
        self.value = [self.subtype() for _ in range(len(value))]
        for i, v in enumerate(self.value):
            v.set_from_json(value[i])

    @property
    def type(self):
        return f"List[{self.subtype.__name__}]"

    def add(self, value):
        if not self.subtype.is_valid(value):
            raise InvalidValue(f"\"{value}\" est incompatible avec le sous-type {self.subtype.__class__.__name__}")
        self.value.append(self.subtype(value))

    def remove(self, value : str):
        if not self.subtype.is_valid(value):
            raise InvalidValue(f"\"{value}\" est incompatible avec le sous-type {self.subtype.__class__.__name__}")
        self.value.remove(self.subtype(value))

    def clear(self):
        self.value = []
