from dataclasses import dataclass
from typing import List, Optional

from sqlfmt.jinjafmt import JinjaFormatter
from sqlfmt.line import Line
from sqlfmt.merger import LineMerger
from sqlfmt.mode import Mode
from sqlfmt.node import Node
from sqlfmt.query import Query
from sqlfmt.splitter import LineSplitter


@dataclass
class QueryFormatter:
    mode: Mode

    def _split_lines(self, lines: List[Line]) -> List[Line]:
        """
        Splits lines to make line depth consistent and syntax
        apparent
        """
        splitter = LineSplitter(mode=self.mode)
        new_lines = []
        for line in lines:
            splits = list(splitter.maybe_split(line))
            new_lines.extend(splits)
        return new_lines

    def _format_jinja(self, lines: List[Line]) -> List[Line]:
        """
        Formats the contents of jinja tags (the code between)
        the curlies by mutating existing jinja nodes
        """
        formatter = JinjaFormatter(mode=self.mode)
        for line in lines:
            formatter.format_line(line)
        return lines

    def _merge_lines(self, lines: List[Line]) -> List[Line]:
        """
        Merge lines to minimize vertical space used by the
        query, while maintaining the syntax hierarchy achieved
        by the splitter
        """
        merger = LineMerger(mode=self.mode)
        lines = merger.maybe_merge_lines(lines)
        return lines

    def _dedent_jinja_blocks(self, lines: List[Line]) -> List[Line]:
        """
        Jinja block tags, like {% if foo %} and {% endif %}, shouldn't
        be printed at their depth, since their contents may be dedented
        farther. This dedents the tags as necessary, in a single pass
        """
        start_node: Optional[Node] = None
        for line in lines:
            if (
                line.is_standalone_jinja_statement
                and line.nodes[0].is_closing_jinja_block
            ):
                assert start_node
                line.nodes[0].open_brackets = start_node.open_brackets

            if line.nodes and line.nodes[-1].open_jinja_blocks:
                start_node = line.nodes[-1].open_jinja_blocks[-1]
                if len(line.open_brackets) < len(start_node.open_brackets):
                    start_node.open_brackets = line.open_brackets

        return lines

    def format(self, raw_query: Query) -> Query:
        """
        Applies 4 transformations to a Query:
        1. Splits lines
        2. Formats jinja tags
        3. Merges lines
        4. Dedents jinja block tags to match their least-indented contents
        """
        lines = raw_query.lines

        pipeline = [
            self._split_lines,
            self._format_jinja,
            self._merge_lines,
            self._dedent_jinja_blocks,
        ]

        for transform in pipeline:
            lines = transform(lines)

        formatted_query = Query(
            source_string=raw_query.source_string,
            line_length=raw_query.line_length,
            lines=lines,
        )

        return formatted_query
