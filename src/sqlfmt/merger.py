from dataclasses import dataclass
from typing import List

from sqlfmt.line import Comment, Line, Node
from sqlfmt.mode import Mode
from sqlfmt.token import TokenType


class CannotMergeException(Exception):
    pass


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

        content_nodes: List[Node] = []
        comments: List[Comment] = []
        last_content_line = lines[0]
        for line in lines:
            # skip over newline nodes
            nodes = [
                node for node in line.nodes if node.token.type != TokenType.NEWLINE
            ]
            if nodes:
                last_content_line = line
                content_nodes.extend(nodes)
            comments.extend(line.comments)

        if not content_nodes:
            raise CannotMergeException("Can't merge only whitespace/newlines")
        elif any([n.formatting_disabled for n in content_nodes]):
            raise CannotMergeException(
                "Can't merge lines containing disabled formatting"
            )
        elif any([n.is_multiline for n in content_nodes[1:]]):
            raise CannotMergeException("Can't merge lines containing multiline nodes")

        # append the final newline from the original set of lines
        content_nodes.append(last_content_line.nodes[-1])

        merged_line = Line.from_nodes(
            previous_node=lines[0].previous_node,
            nodes=content_nodes,
            comments=comments,
        )

        if merged_line.is_too_long(self.mode.line_length):
            raise CannotMergeException("Merged line is too long")

        # append the final newlines from the original set of lines
        trailing_blank_lines: List[Line] = []
        for line in reversed(lines):
            if line.is_blank_line:
                trailing_blank_lines.append(line)
            else:
                break

        return [merged_line] + list(reversed(trailing_blank_lines))

    def maybe_merge_lines(self, lines: List[Line]) -> List[Line]:
        """
        Attempts to merge all passed lines into a single line.

        If that fails, divides the lines into segments, delineated
        by lines of equal depth and recurses on each segment.

        Returns a new list of lines
        """
        if len(lines) <= 1:
            return lines
        else:
            try:
                merged_lines = self.create_merged_line(lines)
                new_lines = merged_lines
            except CannotMergeException:
                # lines can't be merged into a single line, so we take several
                # steps to merge some lines together into a final collection,
                # new_lines
                new_lines = []
                # first: if there are consecutive lines that are the same depth
                # that start with operators, we want to merge those
                partially_merged_lines = self._maybe_merge_lines_split_by_operators(
                    lines
                )
                # if there are multiple segments of equal depth, and
                # we know we can't merge across segments, we should try
                # to merge within each segment
                segments = self._split_into_segments(partially_merged_lines)
                if len(segments) > 1:
                    for segment in segments:
                        new_lines.extend(self.maybe_merge_lines(segment))
                    # if merging of any segment was successful, it is
                    # possible that more merging can be done on a second
                    # pass
                    if len(new_lines) < len(partially_merged_lines):
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
                    new_lines.append(partially_merged_lines[0])
                    if (
                        partially_merged_lines[-1].closes_bracket_from_previous_line
                        or partially_merged_lines[
                            -1
                        ].closes_jinja_block_from_previous_line
                    ) and partially_merged_lines[-1].depth == partially_merged_lines[
                        0
                    ].depth:
                        new_lines.extend(
                            self.maybe_merge_lines(partially_merged_lines[1:-1])
                        )
                        new_lines.append(partially_merged_lines[-1])
                    else:
                        new_lines.extend(
                            self.maybe_merge_lines(partially_merged_lines[1:])
                        )
            finally:
                return new_lines

    def _maybe_merge_lines_split_by_operators(
        self, lines: List[Line], merge_across_low_priority_operators: bool = True
    ) -> List[Line]:
        """
        Tries to merge runs of lines at the same depth as lines[0] that
        start with an operator.
        """
        head = 0
        target_depth = lines[head].depth
        last_line_is_singleton_operator = False
        new_lines: List[Line] = []
        for tail, line in enumerate(lines[1:], start=1):
            if (
                line.depth == target_depth
                and (
                    line.starts_with_operator
                    or line.starts_with_comma
                    or last_line_is_singleton_operator
                )
                and (
                    merge_across_low_priority_operators
                    or not line.starts_with_low_priority_merge_operator
                )
            ):
                # keep going until we hit a line that does not start with
                # an operator
                pass
            else:
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
                            self._maybe_merge_lines_split_by_operators(
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
            if len(line.nodes) == 2 and line.starts_with_operator:
                last_line_is_singleton_operator = True
            else:
                last_line_is_singleton_operator = False

        # we need to try one more time to merge everything after head
        try:
            new_lines.extend(self.create_merged_line(lines[head:]))
        except CannotMergeException:
            if merge_across_low_priority_operators:
                new_lines.extend(
                    self._maybe_merge_lines_split_by_operators(
                        lines[head:], merge_across_low_priority_operators=False
                    )
                )
            else:
                new_lines.extend(lines[head:])
        finally:
            return new_lines

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
                    or line.closes_jinja_block_from_previous_line
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
            return [lines[:]]
