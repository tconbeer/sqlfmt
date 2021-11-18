# inspired by lib2to3/pgen tokenizer, Copyright(c) Python Software Foundation

import re
from abc import ABC, abstractmethod
from typing import Dict

from sqlfmt.exception import SqlfmtError
from sqlfmt.token import TokenType


def group(*choices: str) -> str:
    return "(" + "|".join(choices) + ")"


WHITESPACE: str = r"[ \f\t\r\n]"
WHITESPACES: str = WHITESPACE + "+"
MAYBE_WHITESPACES: str = WHITESPACE + "*"
NEWLINE: str = r"\r?\n"
ANY_BLANK: str = group(WHITESPACES, NEWLINE, r"$")


def expand_spaces(s: str) -> str:
    return s.replace(" ", f"{ANY_BLANK}+")


class SqlfmtParsingError(SqlfmtError):
    pass


class Dialect(ABC):
    """
    Abstract class for a SQL dialect.

    Each dialect should override the PATTERNS dict to define their own grammar.
    Each value in the PATTERNS dict must have a regex group (surrounded by
    parentheses) that matches the token; if the token may be delimited by
    whitespace, that should be defined outside the first group.
    """

    PATTERNS: Dict[TokenType, str] = {}

    def __init__(self) -> None:
        self.programs: Dict[TokenType, re.Pattern] = {
            k: re.compile(MAYBE_WHITESPACES + v, re.IGNORECASE)
            for k, v in self.PATTERNS.items()
        }

    @abstractmethod
    def get_patterns(self) -> Dict[TokenType, str]:
        return self.PATTERNS


class Polyglot(Dialect):
    """
    A universal SQL dialect meant to encompass the common usage of at least
    Postgres, MySQL, BigQuery Standard SQL, Snowflake SQL, SparkSQL.
    """

    PATTERNS: Dict[TokenType, str] = {
        TokenType.FMT_OFF: group(r"(--|#) ?fmt: ?off ?(NEWLINE|$)"),
        TokenType.FMT_ON: group(r"(--|#) ?fmt: ?on ?(NEWLINE|$)"),
        # these only match simple jinja tags, without nesting or potential nesting
        TokenType.JINJA: group(
            r"\{\{[^{}%#]*\}\}",
            r"\{%[^{}%#]*?%\}",
            r"\{\#[^{}%#]*?\#\}",
        ),
        # These match just the start and end of jinja tags, which allows
        # the parser to deal with nesting in a more powerful way than
        # regex allows
        TokenType.JINJA_START: group(r"\{[{%#]"),
        TokenType.JINJA_END: group(r"[}%#]\}"),
        TokenType.QUOTED_NAME: group(
            r"'[^\n']*?'",
            r'"[^\n"]*?"',
            r"`[^\n`]*?`",
        ),
        TokenType.COMMENT: group(
            r"--[^\r\n]*",
            r"#[^\r\n]*",
            r"/\*[^*]*\*+(?:[^/*][^*]*\*+)*/",  # simple block comment
        ),
        TokenType.COMMENT_START: group(r"/\*"),
        TokenType.COMMENT_END: group(r"\*/"),
        TokenType.STATEMENT_START: group(r"case") + group(r"\W", r"$"),
        TokenType.STATEMENT_END: group(r"end") + group(r"\W", r"$"),
        TokenType.STAR: group(r"\*"),
        TokenType.NUMBER: group(
            r"-?\d+\.?\d*",
            r"-?\.\d+",
        ),
        TokenType.BRACKET_OPEN: group(
            r"\[",
            r"\(",
            r"\{",
        ),
        TokenType.BRACKET_CLOSE: group(
            r"\]",
            r"\)",
            r"\}",
        ),
        TokenType.DOUBLE_COLON: group(r"::"),
        TokenType.OPERATOR: group(
            r"<>",
            r"!=",
            r"\|\|",
            r"[+\-*/%&@|^=<>:]=?",
            r"~",
        ),
        TokenType.WORD_OPERATOR: group(
            r"and",
            r"between",
            r"as",
            r"ilike",
            r"in",
            r"is",
            r"isnull",
            r"like",
            r"not",
            r"notnull",
            r"on",
            r"or",
            r"over",
            r"similar",
            r"using",
        )
        + group(r"\W", r"$"),
        TokenType.COMMA: group(r","),
        TokenType.DOT: group(r"\."),
        TokenType.UNTERM_KEYWORD: group(
            expand_spaces(r"with( recursive)?"),
            expand_spaces(r"select( as struct| as value)?( all| top \d+| distinct)?"),
            r"from",
            expand_spaces(r"(natural )?((inner|((left|right|full)( outer)?)) )?join"),
            r"where",
            expand_spaces(r"group by"),
            r"having",
            r"qualify",
            r"window",
            expand_spaces(r"(union|intersect|except)( all|distinct)?"),
            expand_spaces(r"order by"),
            r"limit",
            r"offset",
            expand_spaces(r"fetch (first|next)"),
            expand_spaces(r"for (update|no key update|share|key share)"),
            r"when",
            r"then",
            r"else",
            expand_spaces(r"partition by"),
            expand_spaces(r"rows between"),
        )
        + group(r"\W", r"$"),
        TokenType.NAME: group(r"\w+"),
    }

    def get_patterns(self) -> Dict[TokenType, str]:
        return super().get_patterns()
