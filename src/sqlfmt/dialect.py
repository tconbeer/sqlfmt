# inspired by lib2to3/pgen tokenizer, Copyright(c) Python Software Foundation

import re
from abc import ABC, abstractmethod
from typing import Dict, Iterator, List, Optional

from sqlfmt.exception import SqlfmtError
from sqlfmt.token import Token, TokenType


def group(*choices: str) -> str:
    return "(" + "|".join(choices) + ")"


WHITESPACE: str = r"[ \f\t]"
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
        """
        A dialect must implement a tokenize_line method, which receives a line
        (as a string) and other indicators of the state of the line, and yields Tokens
        """
        pass

    @abstractmethod
    def search_for_token(
        self, token_types: List[TokenType], line: str, lnum: int, skipchars: int = 0
    ) -> Optional[Token]:
        """
        Match the first instance of token_type in line; return None if no match is found
        """
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
        TokenType.STATEMENT_START: group(r"case") + ANY_BLANK,
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
            group(r"and", r"or"),
            group(r"on", r"using"),
        )
        + ANY_BLANK,
        TokenType.COMMA: group(r","),
        TokenType.DOT: group(r"\."),
        TokenType.NEWLINE: group(r"\r?\n"),
        TokenType.UNTERM_KEYWORD: group(
            r"with",
            expand_spaces(r"select( all| top \d+| distinct)?"),
            r"from",
            expand_spaces(r"(natural )?((inner|((left|right|full)( outer)?)) )?join"),
            r"where",
            expand_spaces(r"group by"),
            r"having",
            expand_spaces(r"order by"),
            r"limit",
            r"offset",
            expand_spaces(r"union( all)?"),
            r"when",
            r"then",
            r"else",
            expand_spaces(r"partition by"),
            expand_spaces(r"rows between"),
        )
        + ANY_BLANK,
        TokenType.NAME: group(r"\w+"),
    }

    def tokenize_line(
        self, line: str, lnum: int, skipchars: int = 0
    ) -> Iterator[Token]:
        pos, eol = skipchars, len(line)

        while pos < eol:
            # try to match against each regex, in order
            for token_type, prog in self.programs.items():

                match = prog.match(line, pos)
                if match:
                    start, end = match.span(1)
                    prefix = line[pos:start]
                    spos, epos, pos = (lnum, start), (lnum, end), end
                    token = line[start:end]

                    yield Token(token_type, prefix, token, spos, epos, line)
                    break
            # nothing matched. Either whitespace or an error
            else:
                if line[pos:].strip() == "":
                    pos = eol
                else:
                    raise SqlfmtParsingError(
                        f"Could not parse SQL at {(lnum, pos)}: '{line[pos:].strip()}'"
                    )

    def search_for_token(
        self, token_types: List[TokenType], line: str, lnum: int, skipchars: int = 0
    ) -> Optional[Token]:
        if len(token_types) == 1:
            prog = self.programs[token_types[0]]
        else:
            patterns = [self.PATTERNS[t] for t in token_types]
            prog = re.compile(MAYBE_WHITESPACES + group(*patterns), re.IGNORECASE)

        match = prog.search(line, skipchars)
        if not match:
            return None

        start, end = match.span(1)
        prefix = line[skipchars:start]
        spos, epos = (lnum, start), (lnum, end)
        token = line[start:end]

        if len(token_types) == 1:
            final_type = token_types[0]
        else:
            for t in token_types:
                prog = self.programs[t]
                match = prog.match(line, start)
                if match:
                    final_type = t
                    break

        if final_type:
            return Token(final_type, prefix, token, spos, epos, line)
        else:
            raise SqlfmtParsingError(
                "Internal Error! Matched group of types but not individual type"
            )
