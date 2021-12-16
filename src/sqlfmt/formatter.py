from dataclasses import dataclass
from typing import List

from sqlfmt.line import Line
from sqlfmt.merger import LineMerger
from sqlfmt.mode import Mode
from sqlfmt.query import Query
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

    def _merge_lines(self, lines: List[Line]) -> List[Line]:
        merger = LineMerger(mode=self.mode)
        lines = merger.maybe_merge_lines(lines)
        return lines

    def format(self, raw_query: Query) -> Query:
        """
        Applies 2 transformations to a Query:
        1. Splits lines
        2. Merges lines
        """
        lines = raw_query.lines

        pipeline = [
            self._split_lines,
            self._merge_lines,
        ]

        for transform in pipeline:
            lines = transform(lines)

        formatted_query = Query(
            source_string=raw_query.source_string, mode=raw_query.mode, lines=lines
        )

        return formatted_query
