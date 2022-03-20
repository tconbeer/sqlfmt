from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from sqlfmt.comment import Comment
from sqlfmt.exception import CannotMergeException
from sqlfmt.line import Line
from sqlfmt.mode import Mode
from sqlfmt.node import Node
from sqlfmt.token import TokenType


@dataclass
class LineMerger:
    mode: Mode

    def create_merged_line(self, lines: List[Line]) -> List[Line]:
        """
        Returns a new line by merging together all nodes in lines. Raises an
        exception if the returned line would be too long, would be empty,
        or would attempt to merge a multiline token.
        """

        # if the child is just one below the parent, we're trying to
        # merge a single line.
        if len(lines) == 1:
            return lines

        nodes, comments = self._extract_components(lines)

        merged_line = Line.from_nodes(
            previous_node=lines[0].previous_node,
            nodes=nodes,
            comments=comments,
        )

        if merged_line.is_too_long(self.mode.line_length):
            raise CannotMergeException("Merged line is too long")

        # add in any leading or trailing blank lines
        leading_blank_lines = self._extract_leading_blank_lines(lines)
        trailing_blank_lines = list(
            reversed(self._extract_leading_blank_lines(reversed(lines)))
        )

        return leading_blank_lines + [merged_line] + trailing_blank_lines

    @classmethod
    def _extract_components(cls, lines: List[Line]) -> Tuple[List[Node], List[Comment]]:
        """
        Given a list of lines, return 2 components:
        1. list of all nodes in those lines, with only a single trailing newline
        2. list of all comments in all of those lines
        """
        nodes: List[Node] = []
        comments: List[Comment] = []
        final_newline: Optional[Node] = None
        allow_multiline = True
        for line in lines:
            # skip over newline nodes
            content_nodes = [
                cls._raise_unmergeable(node, allow_multiline)
                for node in line.nodes
                if node.token.type != TokenType.NEWLINE
            ]
            if content_nodes:
                final_newline = line.nodes[-1]
                allow_multiline = False
                nodes.extend(content_nodes)
            comments.extend(line.comments)

        if not nodes or not final_newline:
            raise CannotMergeException("Can't merge only whitespace/newlines")

        nodes.append(final_newline)

        return nodes, comments

    @staticmethod
    def _raise_unmergeable(node: Node, allow_multiline: bool) -> Node:
        """
        Raises a CannotMergeException if the node cannot be merged. Otherwise
        returns the node
        """
        if node.formatting_disabled:
            raise CannotMergeException(
                "Can't merge lines containing disabled formatting"
            )
        elif node.is_semicolon:
            raise CannotMergeException(
                "Can't merge multiple queries onto a single line"
            )
        elif node.is_multiline and not allow_multiline:
            raise CannotMergeException("Can't merge lines containing multiline nodes")
        else:
            return node

    @staticmethod
    def _extract_leading_blank_lines(lines: Iterable[Line]) -> List[Line]:
        leading_blank_lines: List[Line] = []
        for line in lines:
            if line.is_blank_line:
                leading_blank_lines.append(line)
            else:
                break
        return leading_blank_lines

    def maybe_merge_lines(self, lines: List[Line]) -> List[Line]:
        """
        Tries to merge any short lines split by
        operators, and then merges any hierarchical statements
        """
        if len(lines) <= 1:
            return lines
        else:
            return self._maybe_merge_segment(self._maybe_merge_operators(lines))

    def _maybe_merge_segment(self, lines: List[Line]) -> List[Line]:
        """
        Attempts to merge all passed lines into a single line.

        If that fails, divides the lines into segments, delineated
        by lines of equal depth and recurses on each segment.

        Returns a new list of lines
        """

        try:
            new_lines = self.create_merged_line(lines)
        except CannotMergeException:
            # lines can't be merged into a single line, so we take several
            # steps to merge some lines together into a final collection,
            # new_lines
            new_lines = []
            # if there are multiple segments of equal depth, and
            # we know we can't merge across segments, we should try
            # to merge within each segment
            segments = self._split_into_segments(lines)
            if len(segments) > 1:
                for segment in segments:
                    new_lines.extend(self._maybe_merge_segment(segment))
                # if merging of any segment was successful, it is
                # possible that more merging can be done on a second
                # pass
                if len(new_lines) < len(lines):
                    new_lines = self.maybe_merge_lines(new_lines)
            # if there was only a single segment at the depth of the
            # top line, we need to move down one line and try again.
            # Because of the structure of a well-split set of lines,
            # in this case moving down one line is guaranteed to move
            # us in one depth.
            # if the final line of the segment matches the top line,
            # we need to strip that off so we only segment the
            # indented lines
            else:
                new_lines.append(lines[0])
                if self._tail_closes_head(lines):
                    new_lines.extend(self._maybe_merge_segment(lines[1:-1]))
                    new_lines.append(lines[-1])
                else:
                    new_lines.extend(self._maybe_merge_segment(lines[1:]))
        finally:
            return new_lines

    @staticmethod
    def _tail_closes_head(lines: List[Line]) -> bool:
        """
        Returns True only if the last line in lines closes a bracket or
        simple jinja block that is opened by the first line in lines
        """
        if (
            lines[-1].closes_bracket_from_previous_line
            or lines[-1].closes_simple_jinja_block_from_previous_line
        ) and lines[-1].depth == lines[0].depth:
            return True
        else:
            return False

    def _maybe_merge_operators(
        self, lines: List[Line], merge_across_low_priority_operators: bool = True
    ) -> List[Line]:
        """
        Tries to merge runs of lines at the same depth that
        start with an operator.
        """
        head = 0
        target_depth = lines[head].depth
        last_line_is_singleton_operator = False
        new_lines: List[Line] = []
        for tail, line in enumerate(lines[1:], start=1):
            if not self._line_continues_operator_sequence(
                line=line,
                target_depth=target_depth,
                prev_singleton=last_line_is_singleton_operator,
                low_priority_okay=merge_across_low_priority_operators,
            ):
                # try to merge everything above line (from head:tail) into
                # a single line
                try:
                    new_lines.extend(self.create_merged_line(lines[head:tail]))
                except CannotMergeException:
                    # the merged line is probably too long. Try the same section
                    # again, but don't try to merge across word operators. This
                    # helps format complex where and join clauses with comparisons
                    # and logic operators
                    if merge_across_low_priority_operators:
                        new_lines.extend(
                            self._maybe_merge_operators(
                                lines[head:tail],
                                merge_across_low_priority_operators=False,
                            )
                        )
                    else:
                        # we were already not merging across low-priority operators
                        # so it's time to give up and just add the original
                        # lines to the new list
                        new_lines.extend(lines[head:tail])
                finally:
                    # reset the head pointer and start the process over
                    # on the remainder of lines
                    head = tail
                    target_depth = lines[head].depth

            # lines can't end with operators unless it's an operator on a line
            # by itself. If that is the case, we want to try to merge the next
            # line into the group
            last_line_is_singleton_operator = line.is_standalone_operator

        # we need to try one more time to merge everything after head
        try:
            new_lines.extend(self.create_merged_line(lines[head:]))
        except CannotMergeException:
            if merge_across_low_priority_operators:
                new_lines.extend(
                    self._maybe_merge_operators(
                        lines[head:], merge_across_low_priority_operators=False
                    )
                )
            else:
                new_lines.extend(lines[head:])
        finally:
            return new_lines

    @staticmethod
    def _line_continues_operator_sequence(
        line: Line,
        target_depth: Tuple[int, int],
        prev_singleton: bool,
        low_priority_okay: bool,
    ) -> bool:
        """
        Returns true if line and/or the current state indicates that this line is part
        of a sequence of operators
        """
        return (
            line.depth == target_depth
            and (prev_singleton or line.starts_with_operator or line.starts_with_comma)
            and (low_priority_okay or not line.starts_with_low_priority_merge_operator)
        )

    def _split_into_segments(self, lines: List[Line]) -> List[List[Line]]:
        """
        A segment is a list of consecutive lines that are indented from the
        first line.

        This method takes a list of lines and returns a list of segments.

        Is is basically an unfold/corecursion
        """
        if not lines:
            return []

        target_depth = lines[0].depth
        for i, line in enumerate(lines[1:], start=1):
            # scan through the lines until we get back to the
            # depth of the first line
            if line.depth <= target_depth or line.depth[1] < target_depth[1]:
                # if this line starts with a closing bracket,
                # we probably want to include that closing bracket
                # in the same segment as the first line.
                if (
                    line.closes_bracket_from_previous_line
                    or line.closes_simple_jinja_block_from_previous_line
                ) and line.depth == target_depth:
                    idx = i + 1
                    try:
                        segments = [self.create_merged_line(lines[:idx])]
                    except CannotMergeException:
                        # it's possible a line has a closing and open
                        # paren, like ") + (\n". In that case, if
                        # we can't merge the first parens together,
                        # we want to return a segment that can try
                        # to merge the second parens together. To
                        # ensure we don't merge the original opening
                        # bracket into the contents, without the
                        # closing bracket, we need to return the first
                        # line (which must contain the opening bracket)
                        # as its own segment
                        if line.opens_new_bracket:
                            idx = i
                            segments = [lines[:1], lines[1:idx]]
                        else:
                            segments = [lines[:idx]]
                else:
                    idx = i
                    segments = [lines[:idx]]
                return segments + self._split_into_segments(lines[idx:])
        else:
            # we've exhausted lines without finding any segments, so return a
            # single segment comprising the original list
            return [lines]
