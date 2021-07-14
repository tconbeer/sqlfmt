# inspired by lib2to3/pgen tokenizer, Copyright(c) Python Software Foundation

import re
from abc import ABC, abstractmethod
from typing import Dict, Iterator

from sqlfmt.token import Token, TokenType


def group(*choices: str) -> str:
    return "(" + "|".join(choices) + ")"


class Dialect(ABC):
    """Abstract class for a SQL dialect"""

    WHITESPACE: str = r"[ \f\t]*"

    PATTERNS: Dict[TokenType, str] = {
        TokenType.JINJA_START: r"\{[{%#]",
        TokenType.JINJA_END: r"[}%#]\}",
        TokenType.QUOTED_NAME: group(
            r"'[^\n']*'",
            r'"[^\n"]*"',
        ),
        TokenType.COMMENT: r"--[^\r\n]*",
        TokenType.COMMENT_START: r"/\*",
        TokenType.COMMENT_END: r"\*/",
        TokenType.NUMBER: group(
            r"\d+\.?\d*",
            r"\.\d+",
        ),
        TokenType.BRACKET_OPEN: r"(\[|\(|\{)",
        TokenType.BRACKET_CLOSE: r"(\]|\)|\})",
        TokenType.OPERATOR: group(
            r"<>",
            r"!=",
            r"[+\-*/%&@|^=<>:]=?",
            r"~",
        ),
        TokenType.COMMA: r",",
        TokenType.DOT: r"\.",
        TokenType.NEWLINE: r"\r?\n",
        TokenType.TOP_KEYWORD: group(
            r"with",
            r"select( distinct)?",
            r"from",
            r"where",
            r"group by",
            r"having",
            r"union( all)?",
        ),
        TokenType.NAME: r"\w+",
    }

    def __init__(self) -> None:
        self.programs: Dict[TokenType, re.Pattern] = {
            k: re.compile(v) for k, v in self.PATTERNS.items()
        }
        self.all_token_program = re.compile(
            self.WHITESPACE + group(*self.PATTERNS.values())
        )

    @abstractmethod
    def tokenize_line(self, line: str, lnum: int) -> Iterator[Token]:
        """A dialect must implement a tokenize_line method, which receives a line (as a string)
        and other indicators of the state of the line, and yields Tokens"""
        pass


class Postgres(Dialect):
    def tokenize_line(self, line: str, lnum: int) -> Iterator[Token]:
        pos, eol = 0, len(line)

        while pos < eol:
            match = self.all_token_program.match(line, pos)
            if match:
                start, end = match.span(1)
                spos, epos, pos = (lnum, start), (lnum, end), end
                token = line[start:end]

                for token_type, program in self.programs.items():
                    if program.match(token):
                        yield Token(token_type, token, spos, epos, line)
                        break
                else:
                    raise Exception

            else:
                raise Exception
