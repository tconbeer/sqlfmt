# inspired by lib2to3/pgen tokenizer, Copyright(c) Python Software Foundation

import re
from abc import ABC, abstractmethod
from typing import Dict

from sqlfmt.exception import SqlfmtError
from sqlfmt.token import TokenType


def group(*choices: str) -> str:
    return "(" + "|".join(choices) + ")"


WHITESPACE: str = r"\s"
WHITESPACES: str = WHITESPACE + "+"
MAYBE_WHITESPACES: str = r"[^\S\n]" + "*"  # any whitespace except newline
NEWLINE: str = r"\r?\n"
ANY_BLANK: str = group(WHITESPACES, r"$")
EOL = group(NEWLINE, r"$")


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
        TokenType.FMT_OFF: group(r"(--|#) ?fmt: ?off ?") + EOL,
        TokenType.FMT_ON: group(r"(--|#) ?fmt: ?on ?") + EOL,
        # these only match simple jinja tags, without nesting or potential nesting
        TokenType.JINJA_COMMENT: group(
            r"\{\#.*?\#\}",
        ),
        TokenType.JINJA: group(
            r"\{\{[^{}%#]*\}\}",
            r"\{%[^{}%#]*?%\}",
        ),
        # These match just the start and end of jinja tags, which allows
        # the parser to deal with nesting in a more powerful way than
        # regex allows
        TokenType.JINJA_START: group(r"\{[{%]"),
        TokenType.JINJA_END: group(r"[}%]\}"),
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
            r"with(\s+recursive)?",
            r"select(\s+(as\s+struct|as\s+value))?(\s+(all|top\s+\d+|distinct))?",
            r"from",
            r"(natural\s+)?((inner|((left|right|full)(\s+outer)?))\s+)?join",
            r"where",
            r"group\s+by",
            r"having",
            r"qualify",
            r"window",
            r"(union|intersect|except)(\s+all|distinct)?",
            r"order\s+by",
            r"limit",
            r"offset",
            r"fetch\s+(first|next)",
            r"for\s+(update|no\s+key\s+update|share|key\s+share)",
            r"when",
            r"then",
            r"else",
            r"partition\s+by",
            r"rows\s+between",
        )
        + group(r"\W", r"$"),
        TokenType.NAME: group(r"\w+"),
        TokenType.NEWLINE: group(NEWLINE),
    }

    def get_patterns(self) -> Dict[TokenType, str]:
        return super().get_patterns()
