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
        if line.can_be_depth_split and line.contains_multiline_node:
            yield from self.split(line, kind="depth")
        # next, split any long lines
        elif line.can_be_depth_split and line_is_too_long:
            yield from self.split(line, kind="depth")
        # next, split on a change in depth
        elif line.can_be_depth_split and (
            line.change_in_depth != 0
            or (line.contains_unterm_keyword and not line.starts_with_unterm_keyword)
        ):
            yield from self.split(line, kind="depth")
        # split on any comma that doesn't end a line
        elif line.first_comma and line.first_comma < line.last_content_index:
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
            # we want to match indentation of the beginning of head
            # so we have to munge the depth of the comment node in tail
            tail[0].depth = head[0].depth
            if line.previous_node:
                line.previous_node.change_in_depth = (
                    head[0].depth - line.previous_node.depth
                )
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
