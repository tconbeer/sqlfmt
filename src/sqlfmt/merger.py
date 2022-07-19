import itertools
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from sqlfmt.comment import Comment
from sqlfmt.exception import CannotMergeException, SqlfmtSegmentError
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
        if len(lines) <= 1:
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
        elif node.divides_queries:
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
        Tries to merge lines into a single line; if that fails,
        splits lines into segments of equal depth, merges
        runs of operators at that depth, and then recurses into
        each segment

        Returns a new list of Lines
        """
        try:
            merged_lines = self.create_merged_line(lines)
        except CannotMergeException:
            merged_lines = []
            # doesn't fit onto a single line, so split into
            # segments at the depth of lines[0]
            segments = self._split_into_segments(lines)
            # if a segment starts with a standalone operator,
            # the first two lines of that segment should likely
            # be merged before doing anything else
            segments = self._fix_standalone_operators(segments)
            if len(segments) > 1:
                # merge together segments of equal depth that are
                # joined by operators
                segments = self._maybe_merge_operators(segments)
                # some operators really should not be by themselves
                # so if their segments are too long to be merged,
                # we merge just their first line onto the prior segment
                segments = self._maybe_stubbornly_merge(segments)
                # then recurse into each segment and try to merge lines
                # within individual segments
                for segment in segments:
                    merged_lines.extend(self.maybe_merge_lines(segment))
            # if there was only a single segment at the depth of the
            # top line, we need to move down one line and try again.
            # Because of the structure of a well-split set of lines,
            # in this case moving down one line is guaranteed to move
            # us in one depth.
            # if the final line of the segment matches the top line,
            # we need to strip that off so we only segment the
            # indented lines
            else:
                _, i = self._get_first_nonblank_line(lines)
                merged_lines.extend(lines[: i + 1])
                for segment in self._get_remainder_of_segment(lines, i):
                    merged_lines.extend(self.maybe_merge_lines(segment))
        finally:
            return merged_lines

    @classmethod
    def _tail_closes_head(cls, segment: List[Line]) -> bool:
        """
        Returns True only if the last line in lines closes a bracket or
        simple jinja block that is opened by the first line in lines.
        """
        if len(segment) <= 1:
            return False

        head, _ = cls._get_first_nonblank_line(segment)
        tail, _ = cls._get_first_nonblank_line(reversed(segment))
        if head == tail:
            return False
        elif (
            tail.closes_bracket_from_previous_line
            or tail.closes_simple_jinja_block_from_previous_line
        ) and tail.depth == head.depth:
            return True
        else:
            return False

    @staticmethod
    def _get_first_nonblank_line(segment: Iterable[Line]) -> Tuple[Line, int]:
        for i, line in enumerate(segment):
            if not line.is_blank_line:
                return line, i
        else:
            raise SqlfmtSegmentError("All lines in the segment are empty")

    def _fix_standalone_operators(self, segments: List[List[Line]]) -> List[List[Line]]:
        """
        If the first line of a segment is a standalone operator,
        we should try to merge the first two lines together before
        doing anything else
        """
        for segment in segments:
            try:
                head, i = self._get_first_nonblank_line(segment)
                if head.is_standalone_operator:
                    _, j = self._get_first_nonblank_line(segment[i + 1 :])
                    try:
                        merged_lines = self.create_merged_line(segment[: i + j + 2])
                        segment[: i + j + 2] = merged_lines
                    except CannotMergeException:
                        pass
            except SqlfmtSegmentError:
                pass
        return segments

    def _maybe_merge_operators(
        self,
        segments: List[List[Line]],
        priority: int = 2,
    ) -> List[List[Line]]:
        """
        Tries to merge runs of segments that start with operators into previous
        segments. Operators have a priority that determines a sort of hierarchy;
        if we can't merge a whole run of operators, we increase the priority to
        create shorter runs that can be merged
        """
        if len(segments) <= 1 or priority < 0:
            return segments
        head = 0
        new_segments: List[List[Line]] = []

        for i, segment in enumerate(segments[1:], start=1):
            if not self._segment_continues_operator_sequence(segment, priority):
                new_segments.extend(
                    self._try_merge_operator_segments(segments[head:i], priority)
                )
                head = i

        # we need to try one more time to merge everything after head
        else:
            new_segments.extend(
                self._try_merge_operator_segments(segments[head:], priority)
            )

        return new_segments

    @classmethod
    def _segment_continues_operator_sequence(
        cls, segment: List[Line], min_priority: int
    ) -> bool:
        """
        Returns true if the first line of the segment is part
        of a sequence of operators
        """
        try:
            line, _ = cls._get_first_nonblank_line(segment)
        except SqlfmtSegmentError:
            # if a segment is blank, keep scanning
            return True
        else:
            return (
                (
                    line.starts_with_operator
                    and cls._operator_priority(line.nodes[0].token.type) <= min_priority
                )
                or line.starts_with_comma
                or line.starts_with_opening_square_bracket
            )

    @staticmethod
    def _operator_priority(token_type: TokenType) -> int:
        if token_type in (TokenType.BOOLEAN_OPERATOR, TokenType.ON):
            return 2
        elif token_type not in (
            # list of "tight binding" operators
            TokenType.AS,
            TokenType.DOUBLE_COLON,
            TokenType.TIGHT_WORD_OPERATOR,
        ):
            return 1
        else:
            return 0

    def _try_merge_operator_segments(
        self, segments: List[List[Line]], priority: int
    ) -> List[List[Line]]:
        """
        Attempts to merge segments into a single line; if that fails,
        recurses at a lower operator priority
        """
        if len(segments) <= 1:
            return segments

        try:
            new_segments = [self.create_merged_line(list(itertools.chain(*segments)))]
        except CannotMergeException:
            new_segments = self._maybe_merge_operators(segments, priority - 1)
        finally:
            return new_segments

    def _maybe_stubbornly_merge(self, segments: List[List[Line]]) -> List[List[Line]]:
        """
        We prefer some operators, like `as`, `over()`, `exclude()`, and
        array or dictionary accessing with `[]` to be
        forced onto the prior line, even if the contents of their brackets
        don't fit there. This is also true for most operators that open
        a bracket, like `in ()` or `+ ()`, as long as the preceding segment
        does not also start with an operator.

        This method scans for segments that start with
        such operators and partially merges those segments with the prior
        segments by calling _stubbornly_merge()
        """
        if len(segments) <= 1:
            return segments

        new_segments = [segments[0]]
        for segment in segments[1:]:
            prev_operator = self._segment_continues_operator_sequence(
                new_segments[-1], min_priority=1
            )
            if (
                # always stubbornly merge P0 operators (e.g., `over`)
                self._segment_continues_operator_sequence(segment, min_priority=0)
                # stubbornly merge p1 operators only if they do NOT
                # follow another p1 operator AND they open brackets
                # and cover multiple lines
                or (
                    not prev_operator
                    and self._segment_continues_operator_sequence(
                        segment, min_priority=1
                    )
                    and self._tail_closes_head(segment)
                )
            ):
                prev_segment = new_segments.pop()
                merged_segments = self._stubbornly_merge(prev_segment, segment)
                new_segments.extend(merged_segments)
            else:
                new_segments.append(segment)

        return new_segments

    def _stubbornly_merge(
        self, prev_segment: List[Line], segment: List[Line]
    ) -> List[List[Line]]:
        """
        Attempts several different methods of merging prev_segment and
        segment. Returns a list of segments that represent the
        best possible merger of those two segments
        """
        new_segments: List[List[Line]] = []
        # try to merge the first line of this segment with the previous segment
        head, i = self._get_first_nonblank_line(segment)

        try:
            prev_segment = self.create_merged_line(prev_segment + [head])
            prev_segment.extend(segment[i + 1 :])
            new_segments.append(prev_segment)
        except CannotMergeException:
            # try to add this segment to the last line of the previous segment
            last_line, k = self._get_first_nonblank_line(reversed(prev_segment))
            try:
                new_last_lines = self.create_merged_line([last_line] + segment)
                prev_segment[-(k + 1) :] = new_last_lines
                new_segments.append(prev_segment)
            except CannotMergeException:
                # try to add just the first line of this segment to the last
                # line of the previous segment
                try:
                    new_last_lines = self.create_merged_line([last_line, head])
                    prev_segment[-(k + 1) :] = new_last_lines
                    prev_segment.extend(segment[i + 1 :])
                    new_segments.append(prev_segment)
                except CannotMergeException:
                    # give up and just return the original segments
                    return [prev_segment, segment]

        return new_segments

    @classmethod
    def _get_remainder_of_segment(
        cls, segment: List[Line], idx: int
    ) -> List[List[Line]]:
        """
        Takes a segment and an index, and returns a list of either one or two segments,
        composed of the lines of segment[idx+1:], depending on whether the segment
        ends with a closing bracket
        """
        if cls._tail_closes_head(segment):
            _, j = cls._get_first_nonblank_line(reversed(segment))
            return [
                # the lines between the head and tail
                segment[idx + 1 : -(j + 1)],
                # the tail line (and trailing whitespace)
                segment[-(j + 1) :],
            ]
        else:
            return [segment[idx + 1 :]]

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
        head_is_singleton_operator = lines[0].is_standalone_operator
        start_idx = 2 if head_is_singleton_operator else 1
        for i, line in enumerate(lines[start_idx:], start=start_idx):
            # scan through the lines until we get back to the
            # depth of the first line
            if line.depth <= target_depth or line.depth[1] < target_depth[1]:
                # if this line starts with a closing bracket,
                # we want to include that closing bracket
                # in the same segment as the first line.
                if (
                    line.closes_bracket_from_previous_line
                    or line.closes_simple_jinja_block_from_previous_line
                    or line.is_blank_line
                ) and line.depth == target_depth:
                    continue
                else:
                    return [lines[:i]] + self._split_into_segments(lines[i:])
        else:
            # we've exhausted lines without finding any segments, so return a
            # single segment comprising the original list
            return [lines]
