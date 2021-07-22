from dataclasses import dataclass
from typing import Iterator, Optional

from sqlfmt.line import Line
from sqlfmt.mode import Mode
from sqlfmt.token import TokenType


@dataclass
class LineSplitter:
    mode: Mode

    def maybe_split(self, line: Line) -> Iterator[Line]:
        """
        Evaluates a line for splitting. If line matches criteria for splitting,
        yields new lines; otherwise yields original line

        TODO: MAKE THIS LOGIC MORE MODULAR AND CLEAR
        """
        MAX_LENGTH = self.mode.line_length
        length = len(line)

        # first, split a comment onto previous line if the line is too long
        if length > MAX_LENGTH and line.ends_with_comment:
            yield from self.split(line, kind="comment")
        # next, consider splitting on a change in depth, if the line has one
        # that isn't at the start or end of the line
        elif (
            line.depth_split
            and line.depth_split < len(line.nodes) - 1
            and (
                # always split a long line that changes depth at any point
                length > MAX_LENGTH
                # always split a line that indents or dedents midway through.
                # This will split one-liners ("select a\nfrom b" ->
                # "select/n    a\nfrom\n    b") but we'll
                # merge those back together in the next pass if they are short
                # enough
                or line.change_in_depth != 0
            )
        ):
            yield from self.split(line, kind="depth")

        # split on any comma that doesn't end a line
        elif line.first_comma and line.first_comma < len(line.nodes) - 1:
            yield from self.split(line, kind="comma")
        # nothing to split on. TODO: split on long lines with operators or
        # just names
        else:
            yield line

    def split(self, line: Line, kind: str = "depth") -> Iterator[Line]:
        """
        Split this line according to the kind dictated, using the
        highest priority token of each kind. Yields new lines.
        """
        if kind in ("depth", "comment"):
            if not line.depth_split:
                yield line
            else:
                yield from self.split_at_index(line, line.depth_split)
        elif kind == "comma":
            if not line.first_comma:
                yield line
            else:
                yield from self.split_at_index(line, line.first_comma)
        else:
            yield line

    def split_at_index(self, line: Line, index: int) -> Iterator[Line]:
        """
        Split a line before nodes[index]. Recursively maybe_split
        resulting lines. Yields new lines
        """
        assert index > 0, "Cannot split at start of line!"
        head, tail = line.nodes[:index], line.nodes[index:]

        # if we're splitting on a comment, we want the standalone comment
        # line to come first, before the code it is commenting
        comment_line: Optional[Line] = None
        if tail[0].token.type == TokenType.COMMENT:
            comment_line = Line.from_nodes(
                source_string=line.source_string,
                previous_node=line.previous_node,
                nodes=tail,
            )
            yield comment_line

        head_line = Line.from_nodes(
            source_string=line.source_string,
            previous_node=tail[-1] if comment_line else line.previous_node,
            nodes=head,
        )
        head_line.append_newline()
        yield from self.maybe_split(head_line)

        if not comment_line:
            tail_line = Line.from_nodes(
                source_string=line.source_string,
                previous_node=head_line.nodes[-1],
                nodes=tail,
            )
            yield from self.maybe_split(tail_line)
