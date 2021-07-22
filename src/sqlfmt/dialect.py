# inspired by lib2to3/pgen tokenizer, Copyright(c) Python Software Foundation

import re
from abc import ABC, abstractmethod
from typing import Dict, Iterator

from sqlfmt.token import Token, TokenType


def group(*choices: str) -> str:
    return "(" + "|".join(choices) + ")"


WHITESPACE: str = r"[ \f\t]"
WHITESPACES: str = WHITESPACE + "+"
MAYBE_WHITESPACES: str = WHITESPACE + "*"
NEWLINE: str = r"\r?\n"
ANY_BLANK: str = group(WHITESPACES, NEWLINE, r"$")


class Dialect(ABC):
    """
    Abstract class for a SQL dialect.

    Each dialect should override the PATTERNS dict to define their own grammar.
    Each value in the PATTERNS dict have a regex group (surrounded by
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
    def tokenize_line(self, line: str, lnum: int) -> Iterator[Token]:
        """A dialect must implement a tokenize_line method, which receives a line (as a string)
        and other indicators of the state of the line, and yields Tokens"""
        pass


class Postgres(Dialect):

    PATTERNS: Dict[TokenType, str] = {
        TokenType.JINJA: group(
            r"\{\{[^\n]*\}\}",
            r"\{%[^\n]*%\}",
            r"\{\#[^\n]*\#\}",
        ),
        TokenType.JINJA_START: group(r"\{[{%#]"),
        TokenType.JINJA_END: group(r"[}%#]\}"),
        TokenType.QUOTED_NAME: group(
            r"'[^\n']*'",
            r'"[^\n"]*"',
        ),
        TokenType.COMMENT: group(r"--[^\r\n]*"),
        TokenType.COMMENT_START: group(r"/\*"),
        TokenType.COMMENT_END: group(r"\*/"),
        TokenType.STATEMENT_START: group(r"case", r"when") + ANY_BLANK,
        TokenType.STATEMENT_END: group(r"then", r"end(,)?") + ANY_BLANK,
        TokenType.NUMBER: group(
            r"\d+\.?\d*",
            r"\.\d+",
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
            r"[+\-*/%&@|^=<>:]=?",
            r"~",
        ),
        TokenType.COMMA: group(r","),
        TokenType.DOT: group(r"\."),
        TokenType.NEWLINE: group(r"\r?\n"),
        TokenType.TOP_KEYWORD: group(
            r"with",
            r"select( all| top \d+| distinct)?",
            r"from",
            r"where",
            r"group by",
            r"having",
            r"order by",
            r"limit",
            r"offset",
            r"union( all)?",
        )
        + ANY_BLANK,
        TokenType.NAME: group(r"\w+"),
    }

    def tokenize_line(self, line: str, lnum: int) -> Iterator[Token]:
        pos, eol = 0, len(line)

        while pos < eol:
            for token_type, prog in self.programs.items():

                match = prog.match(line, pos)
                if match:
                    start, end = match.span(1)
                    prefix = line[pos:start]
                    spos, epos, pos = (lnum, start), (lnum, end), end
                    token = line[start:end]

                    yield Token(token_type, prefix, token, spos, epos, line)
                    break

            else:
                if line[pos:].strip() == "":
                    pos = eol
                else:
                    match = re.match(WHITESPACES, line[pos:])
                    if match:
                        prefix = match.group(0)
                    else:
                        prefix = ""
                    yield Token(
                        TokenType.ERROR_TOKEN,
                        prefix,
                        line[pos:].strip(),
                        (lnum, pos),
                        (lnum, eol),
                        line,
                    )
                    pos = eol
