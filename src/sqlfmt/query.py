from dataclasses import dataclass, field
from typing import List

from sqlfmt.line import Line
from sqlfmt.node import Node
from sqlfmt.token import Token


@dataclass
class Query:
    """
    A Query is a collection of Lines, the corresponding raw source string, and
    the desired line length. Queries are mutated by the Formatter
    """

    source_string: str
    line_length: int
    lines: List[Line] = field(default_factory=list)

    @property
    def tokens(self) -> List[Token]:
        tokens: List[Token] = []
        for line in self.lines:
            tokens.extend(line.tokens)
        return tokens

    @property
    def nodes(self) -> List[Node]:
        nodes: List[Node] = []
        for line in self.lines:
            nodes.extend(line.nodes)
        return nodes

    def __str__(self) -> str:
        draft = [line.render_with_comments(self.line_length) for line in self.lines]
        return "".join(draft)
