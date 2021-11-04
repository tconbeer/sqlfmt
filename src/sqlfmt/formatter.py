from dataclasses import dataclass
from typing import List

from sqlfmt.line import Line
from sqlfmt.merger import LineMerger
from sqlfmt.mode import Mode
from sqlfmt.parser import Query
from sqlfmt.splitter import LineSplitter


@dataclass
class QueryFormatter:
    mode: Mode

    def _split_lines(self, lines: List[Line]) -> List[Line]:
        splitter = LineSplitter(mode=self.mode)
        new_lines = []
        for line in lines:
            splits = list(splitter.maybe_split(line))
            new_lines.extend(splits)
        return new_lines

    def _indent_standalone_comments(self, lines: List[Line]) -> List[Line]:
        prev_depth = 0
        for line in reversed(lines):
            if line.is_standalone_comment:
                line.depth = prev_depth
            else:
                prev_depth = line.depth
        return lines

    def _merge_lines(self, lines: List[Line]) -> List[Line]:
        merger = LineMerger(mode=self.mode)
        lines = merger.maybe_merge_lines(lines)
        return lines

    def format(self, raw_query: Query) -> Query:
        """
        Applies 3 transformations to a Query:
        1. Splits lines
        2. Merges lines
        3. Fixes indentation of standalone comments
        """
        lines = raw_query.lines

        pipeline = [
            self._split_lines,
            self._indent_standalone_comments,
            self._merge_lines,
            self._indent_standalone_comments,
        ]

        for transform in pipeline:
            lines = transform(lines)

        formatted_query = Query(
            source_string=raw_query.source_string, mode=raw_query.mode, lines=lines
        )

        return formatted_query
