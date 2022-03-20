from dataclasses import dataclass
from typing import Iterator

from sqlfmt.line import Line
from sqlfmt.mode import Mode
from sqlfmt.node import Node


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

        split_after = False
        for i, node in enumerate(line.nodes):
            if node.is_newline:
                # can't split just before a newline
                yield line
                break
            elif i > 0 and (split_after or self.maybe_split_before(node)):
                yield from self.split_at_index(line, i)
                break

            split_after = self.maybe_split_after(node)

    def maybe_split_before(self, node: Node) -> bool:
        """
        Return True if we should split before node
        """
        if (
            # if there is a multiline node on this line and it isn't the
            # only thing on this line, then split before the multiline node
            node.is_multiline
            # always split before any unterm kw
            or node.is_unterm_keyword
            # always split before any opening jinja block
            or node.is_opening_jinja_block
            # always split before any node that decreases depth
            or node.is_closing_bracket
            or node.is_closing_jinja_block
            or node.is_semicolon
        ):
            return True
        # split before any operator unless the previous node is a closing
        # bracket or statement, or it is the "and" following a "between"
        else:
            return self.maybe_split_before_operator(node)

    def maybe_split_before_operator(self, node: Node) -> bool:
        """
        Return true if this node is an operator and it has the
        right context for splitting before it. We do not split before
        operators that follow closing brackets
        """
        return (
            node.is_operator
            and node.previous_node is not None
            and not node.previous_node.is_closing_bracket
            and not node.is_the_and_after_the_between_operator
        )

    def maybe_split_after(self, node: Node) -> bool:
        """
        Return True if we should split after node
        """
        if (
            # always split after any comma that doesn't end a line
            node.is_comma
            # always split after a token that increases depth
            or node.is_opening_bracket
            or node.is_opening_jinja_block
            or node.is_unterm_keyword
        ):
            return True
        else:
            return False

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
        yield head_line

        tail_line = Line.from_nodes(
            previous_node=head_line.nodes[-1],
            nodes=tail,
            comments=[],
        )
        yield from self.maybe_split(tail_line)
