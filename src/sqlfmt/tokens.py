import re
import sys
from enum import Enum, auto
from typing import NamedTuple

if sys.version_info >= (3, 8):
    from functools import cached_property
else:
    from backports.cached_property import cached_property


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

    @cached_property
    def is_jinja_statement(self) -> bool:
        return self in (
            TokenType.JINJA_STATEMENT,
            TokenType.JINJA_BLOCK_START,
            TokenType.JINJA_BLOCK_KEYWORD,
            TokenType.JINJA_BLOCK_END,
        )

    @cached_property
    def is_jinja(self) -> bool:
        return self.is_jinja_statement or self is TokenType.JINJA_EXPRESSION

    @cached_property
    def is_opening_bracket(self) -> bool:
        return self in [
            TokenType.BRACKET_OPEN,
            TokenType.STATEMENT_START,
        ]

    @cached_property
    def divides_queries(self) -> bool:
        return self in [
            TokenType.SEMICOLON,
            TokenType.SET_OPERATOR,
        ]

    @cached_property
    def does_not_set_prev_sql_context(self) -> bool:
        return self.is_jinja_statement or self is TokenType.NEWLINE

    @cached_property
    def is_always_operator(self) -> bool:
        return self in [
            TokenType.OPERATOR,
            TokenType.WORD_OPERATOR,
            TokenType.ON,
            TokenType.BOOLEAN_OPERATOR,
            TokenType.DOUBLE_COLON,
            TokenType.SEMICOLON,
        ]

    @cached_property
    def is_never_preceded_by_space(self) -> bool:
        return self in [
            TokenType.BRACKET_CLOSE,
            TokenType.COLON,
            TokenType.DOUBLE_COLON,
            TokenType.COMMA,
            TokenType.DOT,
            TokenType.NEWLINE,
        ]

    @cached_property
    def is_preceded_by_space_except_after_open_bracket(self) -> bool:
        return self in [
            TokenType.UNTERM_KEYWORD,
            TokenType.STATEMENT_START,
            TokenType.STATEMENT_END,
            TokenType.WORD_OPERATOR,
            TokenType.BOOLEAN_OPERATOR,
            TokenType.ON,
        ]

    @cached_property
    def is_possible_name(self) -> bool:
        return self in [
            TokenType.QUOTED_NAME,
            TokenType.NAME,
            TokenType.STAR,
            TokenType.JINJA_EXPRESSION,
        ]

    @cached_property
    def is_always_lowercased(self) -> bool:
        return self in [
            TokenType.UNTERM_KEYWORD,
            TokenType.BRACKET_OPEN,
            TokenType.STATEMENT_START,
            TokenType.STATEMENT_END,
            TokenType.WORD_OPERATOR,
            TokenType.ON,
            TokenType.BOOLEAN_OPERATOR,
            TokenType.SET_OPERATOR,
        ]

    @cached_property
    def is_equivalent_in_output(self) -> bool:
        return self not in [
            TokenType.NEWLINE,
            TokenType.COMMENT,
        ]


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
