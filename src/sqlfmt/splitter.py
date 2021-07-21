from dataclasses import dataclass
from typing import Iterator, Optional

from sqlfmt.line import Line
from sqlfmt.mode import Mode
from sqlfmt.token import Token, TokenType


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
        if length > MAX_LENGTH and line.ends_with_comment:
            yield from self.split(line, kind="comment")
        elif (
            (
                (line.change_in_depth > 0 and not line.starts_with_top_keyword)
                or (
                    line.change_in_depth > 0
                    and line.starts_with_top_keyword
                    and line.first_comma
                )
                or (line.change_in_depth > 1)
                or line.change_in_depth < 0
                or length > MAX_LENGTH
            )
            and line.first_split
            and line.first_split < len(line.nodes) - 1
        ):
            yield from self.split(line, kind="depth")
        elif line.first_comma and line.first_comma < len(line.nodes) - 1:
            yield from self.split(line, kind="comma")
        else:
            yield line

    def split(self, line: Line, kind: str = "depth") -> Iterator[Line]:
        """
        Split this line at the highest-priority token
        """
        if kind in ("depth", "comment"):
            if not line.first_split:
                yield line
            else:
                yield from self.split_at_index(line, line.first_split)
        elif kind == "comma":
            if not line.first_comma:
                yield line
            else:
                yield from self.split_at_index(line, line.first_comma)
        else:
            yield line

    def split_at_index(self, line: Line, index: int) -> Iterator[Line]:
        """
        Split a line before or after nodes[index]. Yields new lines
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
        nl = Token(
            type=TokenType.NEWLINE,
            prefix="",
            token="\n",
            spos=(head[-1].token.epos[0], head[-1].token.epos[1] + 1),
            epos=(head[-1].token.epos[0], head[-1].token.epos[1] + 2),
            line=head[-1].token.line,
        )
        head_line.append_token(nl)
        yield from self.maybe_split(head_line)

        if not comment_line:
            tail_line = Line.from_nodes(
                source_string=line.source_string,
                previous_node=head_line.nodes[-1],
                nodes=tail,
            )
            yield from self.maybe_split(tail_line)
