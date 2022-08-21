import re
from enum import Enum, auto
from typing import NamedTuple


class TokenType(Enum):
    """
    Tokens are basic elements of SQL syntax; we only care about a small number of
    token types, which correspond to query structure and therefore formatting
    """

    FMT_OFF = auto()
    FMT_ON = auto()
    DATA = auto()
    JINJA_STATEMENT = auto()  # {% ... %}
    JINJA_EXPRESSION = auto()  # {{ ... }}
    JINJA_BLOCK_START = auto()  # {% if ... %}
    JINJA_BLOCK_END = auto()  # {% endif %}
    JINJA_BLOCK_KEYWORD = auto()  # {% else %}
    QUOTED_NAME = auto()
    COMMENT = auto()
    COMMENT_START = auto()
    COMMENT_END = auto()
    SEMICOLON = auto()
    STATEMENT_START = auto()
    STATEMENT_END = auto()
    STAR = auto()
    NUMBER = auto()
    BRACKET_OPEN = auto()
    BRACKET_CLOSE = auto()
    DOUBLE_COLON = auto()
    COLON = auto()
    OPERATOR = auto()
    WORD_OPERATOR = auto()
    ON = auto()
    BOOLEAN_OPERATOR = auto()
    COMMA = auto()
    DOT = auto()
    NEWLINE = auto()
    UNTERM_KEYWORD = auto()  # Unterminated keyword
    SET_OPERATOR = auto()
    NAME = auto()


class Token(NamedTuple):
    """
    Representation of a syntactic element. Tokens always reference their position
    in the source query, and contain the full text of the line from the source
    query. Tokens are immutable, but some operations replace Tokens in order to
    update their type, prefix, or token in the formatted result.
    """

    type: TokenType
    prefix: str
    token: str
    spos: int
    epos: int

    def __str__(self) -> str:
        return f"Token(type={self.type}, token={self.token}, spos={self.spos})"

    def __repr__(self) -> str:
        return (
            f"Token(type={self.type}, "
            f"prefix={repr(self.prefix)}, token={repr(self.token)}, "
            f"spos={self.spos}, epos={self.epos}"
            f")"
        )

    @classmethod
    def from_match(
        cls,
        source_string: str,
        match: re.Match,
        token_type: TokenType,
    ) -> "Token":
        """
        Constructs a Token based on a regex match in a source string, and a type.
        """
        pos, _ = match.span(0)
        spos, epos = match.span(1)
        prefix = source_string[pos:spos]
        token_text = source_string[spos:epos]
        return Token(token_type, prefix, token_text, pos, epos)
