from dataclasses import dataclass, field
from functools import cached_property
from io import StringIO
from typing import List

from sqlfmt.line import Line, Node
from sqlfmt.mode import Mode
from sqlfmt.splitter import LineSplitter
from sqlfmt.token import Token


@dataclass
class Query:
    source_string: str
    mode: Mode
    lines: List[Line] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.tokenize_from_source()
        self.split_and_merge_lines()

    def tokenize_from_source(self) -> None:
        """Updates self.lines and self.tokens from source_string"""
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

    def split_and_merge_lines(self) -> None:
        """
        Mutates self.lines to enforce line length and other splitting
        rules
        """
        splitter = LineSplitter(mode=self.mode)
        new_lines = []
        for line in self.lines:
            splits = list(splitter.maybe_split(line))
            new_lines.extend(splits)
        self.lines = new_lines

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

    @cached_property
    def formatted_string(self) -> str:
        draft = []
        for s in [str(line) for line in self.lines]:
            if s:
                draft.append(s)

        q = "".join(draft)
        return q
