from dataclasses import dataclass
from typing import Iterator, Optional

from sqlfmt.line import Line
from sqlfmt.mode import Mode


@dataclass
class LineSplitter:
    mode: Mode

    def maybe_split(self, line: Line) -> Iterator[Line]:
        """
        Evaluates a line for splitting. If line matches criteria for splitting,
        yields new lines; otherwise yields original line
        """
        line_is_too_long: bool = line.is_too_long(self.mode.line_length)

        # first, if there is a multiline node on this line and it isn't the
        # only thing on this line, then split before the multiline node
        if (
            line.can_be_depth_split or line.can_be_comment_split
        ) and line.contains_multiline_node:
            yield from self.split(line, kind="depth")
        # next, split any long lines
        elif (
            line.can_be_depth_split or line.can_be_comment_split
        ) and line_is_too_long:
            yield from self.split(line, kind="depth")
        # next, if a line changes depth midway, split that line,
        # unless we are only splitting off a comment
        elif line.can_be_depth_split and (
            line.change_in_depth != 0
            or (line.contains_unterm_keyword and not line.starts_with_unterm_keyword)
            or line.closes_bracket_from_previous_line
        ):
            yield from self.split(line, kind="depth")
        # split on any comma that doesn't end a line
        # first_comma points to the index after the comma
        elif line.first_comma and line.first_comma < line.last_content_index + 1:
            yield from self.split(line, kind="comma")
        elif line_is_too_long and line.contains_operator:
            yield from self.split(line, kind="operator")
        # nothing to split on. TODO: split on long lines just names
        else:
            yield line

    def split(self, line: Line, kind: str = "depth") -> Iterator[Line]:
        """
        Split this line according to the kind dictated, using the
        highest priority token of each kind. Yields new lines.
        """
        if kind == "depth":
            if not line.depth_split:
                yield line
            else:
                yield from self.split_at_index(line, line.depth_split)
        elif kind == "comma":
            if not line.first_comma:
                yield line
            else:
                yield from self.split_at_index(line, line.first_comma)
        elif kind == "operator":
            if not line.first_operator:
                yield line
            else:
                yield from self.split_at_index(line, line.first_operator)
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
        if tail[0].is_comment and not tail[0].is_multiline:
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
