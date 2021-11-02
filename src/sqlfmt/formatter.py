from dataclasses import dataclass

from sqlfmt.merger import LineMerger
from sqlfmt.mode import Mode
from sqlfmt.parser import Query
from sqlfmt.splitter import LineSplitter


@dataclass
class QueryFormatter:
    mode: Mode

    def format(self, raw_query: Query) -> Query:
        """
        Applies 3 transformations to a Query:
        1. Splits lines
        2. Merges lines
        3. Fixes indentation of standalone comments
        """
        splitter = LineSplitter(mode=self.mode)
        new_lines = []
        for line in raw_query.lines:
            splits = list(splitter.maybe_split(line))
            new_lines.extend(splits)

        merger = LineMerger(mode=self.mode)
        if new_lines:
            merger.maybe_merge_lines(new_lines)

        # fix indentation of standalone comments
        prev_depth = 0
        for line in reversed(new_lines):
            if line.is_standalone_comment:
                line.depth = prev_depth
            else:
                prev_depth = line.depth

        formatted_query = Query(
            source_string=raw_query.source_string, mode=raw_query.mode, lines=new_lines
        )

        return formatted_query
