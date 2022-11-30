from typing import List, Sequence, Tuple

from sqlfmt.exception import SqlfmtSegmentError
from sqlfmt.line import Line


def create_segments_from_lines(lines: Sequence[Line]) -> List["Segment"]:
    """
    A segment is a list of consecutive lines that are indented from the
    first line.

    This method takes a list of lines and returns a list of segments.

    Is is basically an unfold/corecursion, but due to recursion limits
    we need to do it as a loop.
    """
    segments: List["Segment"] = []
    j = 0

    while True:
        if not lines[j:]:
            return segments

        target_depth = lines[j].depth
        start_idx = j + 2 if lines[j].is_standalone_operator else j + 1
        for i, line in enumerate(lines[start_idx:], start=start_idx):
            # scan through the lines until we get back to the
            # depth of the first line
            if line.starts_new_segment(target_depth):
                segments.append(Segment(lines[j:i]))
                j = i
                break
        else:
            # we've exhausted lines without finding any segments, so append a
            # single segment comprising the original list
            segments.append(Segment(lines[j:]))
            break

    return segments


class Segment(List[Line]):
    @property
    def head(self) -> Tuple[Line, int]:
        """
        Returns the first nonblank line in the Segment, and the index
        of that line
        """
        for i, line in enumerate(self):
            if not line.is_blank_line:
                return line, i
        else:
            raise SqlfmtSegmentError("All lines in the segment are empty")

    @property
    def tail(self) -> Tuple[Line, int]:
        """
        Returns the last nonblank line in the Segment, and the index
        of that line (from the bottom. TODO: make the index more obvious)
        """
        for i, line in enumerate(reversed(self)):
            if not line.is_blank_line:
                return line, i
        else:
            raise SqlfmtSegmentError("All lines in the segment are empty")

    @property
    def tail_closes_head(self) -> bool:
        """
        Returns True only if the last line in the segment closes a bracket or
        simple jinja block that is opened by the first line in the segment.
        """
        if len(self) <= 1:
            return False

        try:
            head, i = self.head
            tail, j = self.tail
        except SqlfmtSegmentError:
            return False

        if head == tail:
            return False

        between_lines = self[i + 1 : -(j + 1)]
        if tail.depth == head.depth and (
            (
                tail.closes_bracket_from_previous_line
                and all([line.depth[0] > head.depth[0] for line in between_lines])
            )
            or (
                tail.closes_simple_jinja_block_from_previous_line
                and all([line.depth[1] > head.depth[1] for line in between_lines])
            )
        ):
            return True
        else:
            return False

    def split_after(self, idx: int) -> List["Segment"]:
        """
        Takes an index, and returns a list of either one or two segments,
        composed of the lines of self.lines[idx+1:], depending on whether the segment
        ends with a closing bracket
        """
        if self.tail_closes_head:
            _, j = self.tail
            return [
                # the lines between the head and tail
                Segment(self[idx + 1 : -(j + 1)]),
                # the tail line (and trailing whitespace)
                Segment(self[-(j + 1) :]),
            ]
        else:
            return [Segment(self[idx + 1 :])]
