from dataclasses import dataclass
from typing import Iterator

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

        if line.formatting_disabled:
            yield line
            return

        has_preceding_comma = False
        has_depth_increasing_node = False
        for i, node in enumerate(line.nodes):
            if node.is_newline:
                # can't split just before a newline
                break
            # split after any node that increases depth unless we're at EOL
            elif has_depth_increasing_node or has_preceding_comma:
                yield from self.split_at_index(line, i)
                return
            # if there is a multiline node on this line and it isn't the
            # only thing on this line, then split before the multiline node
            if i > 0 and node.is_multiline:
                yield from self.split_at_index(line, i)
                return
            # we always split after any comma that doesn't end a line
            elif node.is_comma:
                has_preceding_comma = True
            # always split before any unterm kw or jinja block unless it starts a line
            elif i > 0 and (node.is_unterm_keyword or node.is_opening_jinja_block):
                yield from self.split_at_index(line, i)
                return
            # always split before any node that decreases depth
            elif i > 0 and (node.is_closing_bracket or node.is_closing_jinja_block):
                yield from self.split_at_index(line, i)
                return
            elif (
                node.is_opening_bracket
                or node.is_opening_jinja_block
                or node.is_unterm_keyword
            ):
                has_depth_increasing_node = True
            # split before any operator unless the previous node is a closing
            # bracket or statement
            elif (
                i > 0
                and node.is_operator
                and node.previous_node
                and not node.previous_node.is_closing_bracket
            ):
                yield from self.split_at_index(line, i)
                return

        yield line

    def split_at_index(self, line: Line, index: int) -> Iterator[Line]:
        """
        Split a line before nodes[index]. Recursively maybe_split
        resulting lines. Yields new lines
        """
        assert index > 0, "Cannot split at start of line!"
        head, tail = line.nodes[:index], line.nodes[index:]
        assert head[0] is not None, "Cannot split at start of line!"

        head_line = Line.from_nodes(
            previous_node=line.previous_node,
            nodes=head,
            comments=line.comments,
        )
        head_line.append_newline()
        yield from self.maybe_split(head_line)

        tail_line = Line.from_nodes(
            previous_node=head_line.nodes[-1],
            nodes=tail,
            comments=[],
        )
        yield from self.maybe_split(tail_line)
