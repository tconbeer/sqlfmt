from dataclasses import dataclass

from sqlfmt.merger import LineMerger
from sqlfmt.mode import Mode
from sqlfmt.parser import Query
from sqlfmt.splitter import LineSplitter


@dataclass
class QueryFormatter:
    mode: Mode

    def format(self, raw_query: Query) -> Query:
        """"""
        splitter = LineSplitter(mode=self.mode)
        new_lines = []
        for line in raw_query.lines:
            splits = list(splitter.maybe_split(line))
            new_lines.extend(splits)

        merger = LineMerger(mode=self.mode)
        if new_lines:
            merger.maybe_merge_lines(new_lines)

        formatted_query = Query(
            source_string=raw_query.source_string, mode=raw_query.mode, lines=new_lines
        )

        return formatted_query
