from dataclasses import dataclass, field
from io import StringIO
from typing import List

from sqlfmt.line import Line, Node
from sqlfmt.mode import Mode
from sqlfmt.token import Token


@dataclass
class Query:
    source_string: str
    mode: Mode
    lines: List[Line] = field(default_factory=list)

    @classmethod
    def from_source(cls, source_string: str, mode: Mode) -> "Query":
        q = Query(source_string, mode)
        q.tokenize_from_source()
        return q

    def tokenize_from_source(self) -> None:
        """Updates self.lines from source_string"""
        if not self.source_string:
            return

        if self.lines and self.tokens:
            # don't run this again
            return

        buffer = StringIO(self.source_string)

        for lnum, line in enumerate(buffer.readlines()):
            current_line = Line(
                source_string=line,
                previous_node=self.lines[-1].nodes[-1] if self.lines else None,
            )
            for token in self.mode.dialect.tokenize_line(line=line, lnum=lnum):
                # nodes are formatted as tokens are appended,
                # but splitting lines happens later
                current_line.append_token(token)

            self.lines.append(current_line)

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
        draft = []
        for s in [str(line) for line in self.lines]:
            if s:
                draft.append(s)

        q = "".join(draft)
        return q
