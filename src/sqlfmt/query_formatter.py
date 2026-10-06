from dataclasses import dataclass
from typing import Callable, List, Optional

from sqlfmt.jinjafmt import JinjaFormatter
from sqlfmt.line import Line
from sqlfmt.merger import LineMerger
from sqlfmt.mode import Mode
from sqlfmt.node import FORCE_SPLIT_CLAUSE_KEYWORDS, Node
from sqlfmt.node_manager import NodeManager
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
        node_manager = NodeManager(self.mode.dialect.case_sensitive_names)
        splitter = LineSplitter(node_manager)
        new_lines = []
        for line in lines:
            splits = list(splitter.maybe_split(line))
            new_lines.extend(splits)
        return new_lines

    def _format_jinja(self, lines: List[Line]) -> List[Line]:
        """
        Formats the contents of jinja tags (the code between
        the curlies) by mutating existing jinja nodes
        """
        formatter = JinjaFormatter(mode=self.mode)
        new_lines: List[Line] = []
        for line in lines:
            new_lines.extend(formatter.format_line(line))
        return new_lines

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
                and not line.formatting_disabled
            ):
                assert start_node
                line.nodes[0].open_brackets = start_node.open_brackets

            if line.nodes and line.nodes[-1].open_jinja_blocks:
                start_node = line.nodes[-1].open_jinja_blocks[-1]
                if (
                    len(line.open_brackets) < len(start_node.open_brackets)
                    and not start_node.formatting_disabled
                ):
                    start_node.open_brackets = line.open_brackets

        return lines

    def _force_split_multi_item_clauses(self, lines: List[Line]) -> List[Line]:
        """
        where/having/group by clauses with more than one item (multiple
        boolean-joined conditions, or multiple group-by columns) must
        always split one item per line, even if the whole clause would fit
        on one line -- unlike every other comma/operator list, which only
        breaks when it's too long. The merger has already collapsed
        everything it can onto single Lines by this point, so this pass
        re-expands just the clause Lines that need it.
        """
        new_lines: List[Line] = []
        for line in lines:
            new_lines.extend(self._maybe_split_clause_line(line))
        return new_lines

    def _maybe_split_clause_line(self, line: Line) -> List[Line]:
        if not line.nodes or not line.nodes[0].is_unterm_keyword:
            return [line]

        keyword_node = line.nodes[0]
        keyword = keyword_node.value.split(" ", 1)[0]
        if keyword not in FORCE_SPLIT_CLAUSE_KEYWORDS:
            return [line]

        child_depth = (keyword_node.depth[0] + 1, keyword_node.depth[1])
        is_group_by = keyword == "group"

        def is_item_separator(node: Node) -> bool:
            if node.depth != child_depth:
                return False
            if is_group_by:
                return node.is_comma
            else:
                return (
                    node.is_boolean_operator
                    and node.value in ("and", "or")
                    and not node.is_the_and_after_the_between_operator
                )

        groups: List[List[Node]] = [[]]
        for node in line.nodes[1:]:
            if node.is_newline:
                continue
            if is_group_by and is_item_separator(node):
                # trailing comma stays with the item it follows
                groups[-1].append(node)
                groups.append([])
                continue
            if not is_group_by and is_item_separator(node):
                # and/or leads the next item's line
                groups.append([])
            groups[-1].append(node)

        groups = [g for g in groups if g]
        if not groups:
            return [line]
        groups[0] = [keyword_node] + groups[0]

        if len(groups) <= 1:
            return [line]

        node_manager = NodeManager(self.mode.dialect.case_sensitive_names)
        new_lines: List[Line] = []
        prev_node = line.previous_node
        for group in groups:
            new_line = Line.from_nodes(
                previous_node=prev_node, nodes=group, comments=[]
            )
            node_manager.append_newline(new_line)
            new_lines.append(new_line)
            prev_node = new_line.nodes[-1]

        if line.comments:
            new_lines[-1].comments.extend(line.comments)

        return new_lines

    def _insert_blank_lines(self, lines: List[Line]) -> List[Line]:
        """
        Inserts a blank Line before any Line that starts a new top-level
        clause of a select statement (select/from/where/group by/having/
        order by/qualify/limit), or a set operator (union/union all/
        intersect/except), so each clause is visually separated from its
        neighbors (this also applies recursively to any subquery, since
        the check is structural rather than tied to a particular depth).

        Skips insertion when there's nothing above to separate from (start
        of the query, or this clause is the first content immediately
        inside a newly-opened bracket), or when a blank line is already
        present (so this pass is idempotent and composes cleanly with
        _remove_extra_blank_lines).
        """
        node_manager = NodeManager(self.mode.dialect.case_sensitive_names)
        new_lines: List[Line] = []
        for line in lines:
            if (
                line.starts_new_major_clause
                and not line.formatting_disabled
                and new_lines
                and not new_lines[-1].is_blank_line
                and not new_lines[-1].opens_new_bracket
            ):
                blank_line = Line(previous_node=line.previous_node)
                node_manager.append_newline(blank_line)
                new_lines.append(blank_line)
            new_lines.append(line)
        return new_lines

    def _remove_extra_blank_lines(self, lines: List[Line]) -> List[Line]:
        """
        A query can have at most 2 consecutive blank lines at depth (0,0)
        and 1 consecutive blank line at any other depth. See issue #249
        for motivation and details.
        """
        new_lines: List[Line] = []
        # initialize cnt high so we remove any extra lines at the beginning
        # of files.
        cnt = 2
        for line in lines:
            if line.is_blank_line:
                max_cnt = 2 if line.depth == (0, 0) else 1
                if cnt < max_cnt or line.formatting_disabled:
                    new_lines.append(line)
                cnt += 1
            else:
                new_lines.append(line)
                cnt = 0
        return new_lines

    def format(self, raw_query: Query) -> Query:
        """
        Applies 4 transformations to a Query:
        1. Splits lines
        2. Formats jinja tags
        3. Dedents jinja block tags to match their least-indented contents
        4. Merges lines
        5. Removes extra blank lines
        """
        lines = raw_query.lines

        pipeline: List[Callable[[List[Line]], List[Line]]] = [
            self._split_lines,
            self._format_jinja,
            self._dedent_jinja_blocks,
            self._merge_lines,
            self._force_split_multi_item_clauses,
            self._insert_blank_lines,
            self._remove_extra_blank_lines,
        ]

        for transform in pipeline:
            lines = transform(lines)

        formatted_query = Query(
            source_string=raw_query.source_string,
            line_length=raw_query.line_length,
            lines=lines,
        )

        return formatted_query
