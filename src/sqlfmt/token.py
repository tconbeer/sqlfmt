from collections import namedtuple
from enum import Enum, auto

Token = namedtuple("Token", ["type", "token", "spos", "epos", "line"])


class TokenType(Enum):
    JINJA_START = auto()
    JINJA_END = auto()
    QUOTED_NAME = auto()
    COMMENT = auto()
    COMMENT_START = auto()
    COMMENT_END = auto()
    NUMBER = auto()
    BRACKET_OPEN = auto()
    BRACKET_CLOSE = auto()
    OPERATOR = auto()
    COMMA = auto()
    DOT = auto()
    NEWLINE = auto()
    TOP_KEYWORD = auto()
    NAME = auto()
