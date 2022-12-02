import itertools
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from sqlfmt.comment import Comment
from sqlfmt.exception import CannotMergeException, SqlfmtSegmentError
from sqlfmt.line import Line
from sqlfmt.mode import Mode
from sqlfmt.node import Node
from sqlfmt.operator_precedence import OperatorPrecedence
from sqlfmt.segment import Segment, create_segments_from_lines


@dataclass
class LineMerger:
    mode: Mode

    def create_merged_line(self, lines: List[Line]) -> List[Line]:
        """
        Returns a new line by merging together all nodes in lines. Raises an
        exception if the returned line would be too long, empty, or the nodes in
        any of the lines violate the rules in _raise_unmergeable.
        """

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

    def safe_create_merged_line(self, lines: List[Line]) -> List[Line]:
        try:
            return self.create_merged_line(lines)
        except CannotMergeException:
            return lines

    @classmethod
    def _extract_components(
        cls, lines: Iterable[Line]
    ) -> Tuple[List[Node], List[Comment]]:
        """
        Given a list of lines, return 2 components:
        1. list of all nodes in those lines, with only a single trailing newline
        2. list of all comments in all of those lines
        """
        nodes: List[Node] = []
        comments: List[Comment] = []
        final_newline: Optional[Node] = None
        allow_multiline_jinja = True
        for line in lines:
            # skip over newline nodes
            content_nodes = [
                cls._raise_unmergeable(node, allow_multiline_jinja)
                for node in line.nodes
                if not node.is_newline
            ]
            if content_nodes:
                final_newline = line.nodes[-1]
                nodes.extend(content_nodes)
                # we can merge lines containing multiline jinja nodes iff:
                # 1. the multiline node is on the first line (allow_multiline
                #    is initialized to True)
                # 2. the multiline node is on the second line and follows a
                #    standalone operator
                if not (
                    allow_multiline_jinja
                    and len(content_nodes) == 1
                    and content_nodes[0].is_operator
                ):
                    allow_multiline_jinja = False
            comments.extend(line.comments)

        if not nodes or not final_newline:
            raise CannotMergeException("Can't merge only whitespace/newlines")

        nodes.append(final_newline)

        return nodes, comments

    @staticmethod
    def _raise_unmergeable(node: Node, allow_multiline_jinja: bool) -> Node:
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
        elif node.is_multiline_jinja and not allow_multiline_jinja:
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
            segments = create_segments_from_lines(lines)
            # if a segment starts with a standalone operator,
            # the first two lines of that segment should likely
            # be merged before doing anything else
            segments = self._fix_standalone_operators(segments)
            if len(segments) > 1:
                # merge together segments of equal depth that are
                # joined by operators
                segments = self._maybe_merge_operators(
                    segments, OperatorPrecedence.tiers()
                )
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
                only_segment = segments[0]
                try:
                    _, i = only_segment.head
                except SqlfmtSegmentError:
                    merged_lines.extend(only_segment)
                else:
                    merged_lines.extend(only_segment[: i + 1])
                    for segment in only_segment.split_after(i):
                        merged_lines.extend(self.maybe_merge_lines(segment))

        return merged_lines

    def _fix_standalone_operators(self, segments: List[Segment]) -> List[Segment]:
        """
        If the first line of a segment is a standalone operator,
        we should try to merge the first two lines together before
        doing anything else
        """
        for segment in segments:
            try:
                head, i = segment.head
                if head.is_standalone_operator:
                    remainder_after_operator = Segment(segment[i + 1 :])
                    _, j = remainder_after_operator.head
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
        segments: List[Segment],
        op_tiers: List[OperatorPrecedence],
    ) -> List[Segment]:
        """
        Tries to merge runs of segments that start with operators into previous
        segments. Operators have a priority that determines a sort of hierarchy;
        if we can't merge a whole run of operators, we increase the priority to
        create shorter runs that can be merged
        """
        if len(segments) <= 1 or not op_tiers:
            return segments
        head = 0
        new_segments: List[Segment] = []
        precedence = op_tiers.pop()

        for i, segment in enumerate(segments[1:], start=1):
            if not self._segment_continues_operator_sequence(segment, precedence):
                new_segments.extend(
                    self._try_merge_operator_segments(segments[head:i], op_tiers.copy())
                )
                head = i

        # we need to try one more time to merge everything after head
        else:
            new_segments.extend(
                self._try_merge_operator_segments(segments[head:], op_tiers.copy())
            )

        return new_segments

    @classmethod
    def _segment_continues_operator_sequence(
        cls, segment: Segment, max_precedence: OperatorPrecedence
    ) -> bool:
        """
        Returns true if the first line of the segment is part
        of a sequence of operators of priority <= max_priority
        """
        try:
            line, _ = segment.head
        except SqlfmtSegmentError:
            # if a segment is blank, keep scanning
            return True
        else:
            return (
                line.starts_with_operator
                and OperatorPrecedence.from_node(line.nodes[0]) <= max_precedence
            ) or line.starts_with_comma

    def _try_merge_operator_segments(
        self, segments: List[Segment], op_tiers: List[OperatorPrecedence]
    ) -> List[Segment]:
        """
        Attempts to merge segments into a single line; if that fails,
        recurses at a lower operator priority
        """
        if len(segments) <= 1:
            return segments

        try:
            new_segments = [
                Segment(self.create_merged_line(list(itertools.chain(*segments))))
            ]
        except CannotMergeException:
            new_segments = self._maybe_merge_operators(segments, op_tiers)

        return new_segments

    def _maybe_stubbornly_merge(self, segments: List[Segment]) -> List[Segment]:
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

        # first stubborn-merge all p0 operators
        for i, segment in enumerate(segments[1:], start=1):
            if (
                # always stubbornly merge P0 operators (e.g., `over`)
                self._segment_continues_operator_sequence(
                    segment, max_precedence=OperatorPrecedence.OTHER_TIGHT
                )
            ):
                new_segments = self._stubbornly_merge(new_segments, segment)
            else:
                new_segments.append(segment)

        if len(new_segments) == 1:
            return new_segments

        # next, stubbon-merge qualifying p1 operators
        segments = new_segments
        new_segments = [segments[0]]

        starts_with_p1_operator = [
            self._segment_continues_operator_sequence(
                segment, max_precedence=OperatorPrecedence.COMPARATORS
            )
            for segment in segments
        ]
        for i, segment in enumerate(segments[1:], start=1):
            if (
                not starts_with_p1_operator[i - 1]
                and starts_with_p1_operator[i]
                and Segment(self.safe_create_merged_line(segment)).tail_closes_head
            ):
                new_segments = self._stubbornly_merge(new_segments, segment)
            else:
                new_segments.append(segment)

        return new_segments

    def _stubbornly_merge(
        self, prev_segments: List[Segment], segment: Segment
    ) -> List[Segment]:
        """
        Attempts several different methods of merging the last segment in
        new_segments and segment. Returns a list of segments that represent the
        best possible merger of those segments
        """
        new_segments = prev_segments.copy()
        prev_segment = new_segments.pop()
        try:
            head, i = segment.head
        except SqlfmtSegmentError:
            new_segments.extend([prev_segment, segment])
            return new_segments

        # try to merge the first line of this segment with the previous segment
        try:
            prev_segment = Segment(self.create_merged_line(prev_segment + [head]))
            prev_segment.extend(segment[i + 1 :])
            new_segments.append(prev_segment)
        except CannotMergeException:
            # try to add this segment to the last line of the previous segment
            last_line, k = prev_segment.tail
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
                    new_segments.extend([prev_segment, segment])

        return new_segments
