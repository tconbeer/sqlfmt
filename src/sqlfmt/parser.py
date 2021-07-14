from dataclasses import dataclass, field
from functools import cached_property
from io import StringIO
from typing import List

from sqlfmt.dialect import Dialect
from sqlfmt.token import Token


@dataclass
class Query:
    source_string: str
    dialect: Dialect
    lines: List[str] = field(default_factory=list)
    tokens: List[Token] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.tokenize()

    def tokenize(self) -> None:
        """Updates self.lines and self.tokens from source_string"""
        if not self.source_string:
            return

        buffer = StringIO(self.source_string)
        lnum = 0

        for line in buffer.readlines():
            self.lines.append(line)
            for token in self.dialect.tokenize_line(line=line, lnum=lnum):
                self.tokens.append(token)
            lnum += 1

    @cached_property
    def formatted_string(self) -> str:
        return self.source_string
