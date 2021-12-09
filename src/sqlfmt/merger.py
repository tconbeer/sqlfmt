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

    def create_merged_line(self, lines: List[Line]) -> Line:
        """
        Returns a new line by merging together all nodes in lines. Raises an
        exception if the returned line would be too long, would be empty,
        or would attempt to merge a multiline token.
        """

        # if the child is just one below the parent, we're trying to
        # merge a single line.
        if len(lines) == 1:
            return lines[0]

        content_nodes: List[Node] = []
        comments: List[Comment] = []
        for line in lines:
            # skip over nodes containing NEWLINEs
            nodes = [
                node for node in line.nodes if node.token.type != TokenType.NEWLINE
            ]
            content_nodes.extend(nodes)
            comments.extend(line.comments)

        if not content_nodes:
            raise CannotMergeException("Can't merge only whitespace/newlines")
        elif any([n.is_multiline or n.formatting_disabled for n in content_nodes]):
            raise CannotMergeException(
                "Can't merge lines containing multiline nodes or disabled formatting"
            )

        merged_line = Line.from_nodes(
            source_string=lines[0].source_string,
            previous_node=lines[0].previous_node,
            nodes=content_nodes,
            comments=comments,
        )

        merged_line.append_newline()

        if merged_line.is_too_long(self.mode.line_length):
            raise CannotMergeException("Merged line is too long")

        return merged_line

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
            if line.depth <= target_depth:
                if (
                    line.closes_bracket_from_previous_line
                    and line.depth == target_depth
                ):
                    idx = i + 1
                else:
                    idx = i
                return [lines[:idx]] + self._split_into_segments(lines[idx:])
        else:
            return [lines[:]]

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
                merged_line = self.create_merged_line(lines)
                new_lines = [merged_line]
            except CannotMergeException:
                new_lines = []
                segments = self._split_into_segments(lines)
                # if there are multiple segments of equal depth, and
                # we know we can't merge across segments, we should try
                # to merge within each segment
                if len(segments) > 1:
                    for segment in segments:
                        new_lines.extend(self.maybe_merge_lines(segment))
                    # if merging of any segment was successful, it is
                    # possible that more merging can be done on a second
                    # pass
                    if len(new_lines) < len(lines):
                        new_lines = self.maybe_merge_lines(new_lines)
                    # at this point, new_lines is pretty well merged,
                    # but it is possible to have consecutive lines that
                    # are the same depth that need further merging; namely,
                    # if there are lines that start with operators, it's possible
                    # they can be merged together
                    new_lines = self._maybe_merge_lines_split_by_operators(new_lines)
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
                    if (
                        lines[-1].closes_bracket_from_previous_line
                        and lines[-1].depth == lines[0].depth
                    ):
                        new_lines.extend(self.maybe_merge_lines(lines[1:-1]))
                        new_lines.append(lines[-1])
                    else:
                        new_lines.extend(self.maybe_merge_lines(lines[1:]))
            finally:
                return new_lines

    def _maybe_merge_lines_split_by_operators(self, lines: List[Line]) -> List[Line]:
        """
        Tries to merge runs of lines at the same depth as lines[0] that
        start with an operator
        """
        target_depth = lines[0].depth
        head = 0
        new_lines: List[Line] = []
        assert not lines[0].starts_with_operator
        for tail, line in enumerate(lines[1:], start=1):
            if line.depth == target_depth and line.starts_with_operator:
                continue
            else:
                try:
                    new_lines.append(self.create_merged_line(lines[head:tail]))
                except CannotMergeException:
                    new_lines.extend(lines[head:tail])
                finally:
                    head = tail
        try:
            new_lines.append(self.create_merged_line(lines[head:]))
        except CannotMergeException:
            new_lines.extend(lines[head:])
        finally:
            return new_lines
