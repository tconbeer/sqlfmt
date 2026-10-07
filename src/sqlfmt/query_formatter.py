from dataclasses import dataclass
from typing import Callable, List, Optional

from sqlfmt.jinjafmt import JinjaFormatter
from sqlfmt.line import Line
from sqlfmt.merger import LineMerger
from sqlfmt.mode import Mode
from sqlfmt.node import (
    FORCE_SPLIT_CLAUSE_KEYWORDS,
    Node,
    get_previous_node,
    get_previous_token,
)
from sqlfmt.node_manager import NodeManager
from sqlfmt.query import Query
from sqlfmt.splitter import LineSplitter
from sqlfmt.tokens import TokenType


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

    def _remove_semicolons(self, lines: List[Line]) -> List[Line]:
        """
        The house style never prints semicolons (dbt models are single
        bare statements), so Lines whose only content is a semicolon are
        dropped entirely. Any following major clause (e.g. a second
        statement's `select`) still gets its usual blank-line separation
        from _insert_blank_lines, since that stage runs after this one.
        """
        return [line for line in lines if not line.is_semicolon_only]

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

    def _force_split_join_on_clauses(self, lines: List[Line]) -> List[Line]:
        """
        A join's "on" condition always drops to its own line below the
        join keyword and table reference, regardless of whether the whole
        thing would fit on one line (unlike where/having, which only force
        -split when there's more than one condition). Multiple and/or
        -joined "on" conditions stack one per line, same as where/having.

        When the join clause is too long to fit on one line, the merger's
        existing operator-precedence-aware segment merging already
        produces exactly this shape on its own (on/and/or each get their
        own line, since ON is the tightest-binding operator tier) -- this
        pass only has work to do when the merger successfully collapsed
        the whole join (keyword + table ref + on + conditions) onto a
        single Line because it was short enough to fit.
        """
        new_lines: List[Line] = []
        for line in lines:
            new_lines.extend(self._maybe_split_join_line(line))
        return new_lines

    def _maybe_split_join_line(self, line: Line) -> List[Line]:
        if not line.nodes or not line.nodes[0].is_unterm_keyword:
            return [line]

        keyword_node = line.nodes[0]
        if not keyword_node.value.endswith("join"):
            return [line]

        child_depth = (keyword_node.depth[0] + 1, keyword_node.depth[1])

        def is_on(node: Node) -> bool:
            return node.depth == child_depth and node.token.type is TokenType.ON

        if not any(is_on(node) for node in line.nodes[1:]):
            return [line]

        def is_and_or(node: Node) -> bool:
            return (
                node.depth == child_depth
                and node.is_boolean_operator
                and node.value in ("and", "or")
                and not node.is_the_and_after_the_between_operator
            )

        groups: List[List[Node]] = [[]]
        on_seen = False
        for node in line.nodes[1:]:
            if node.is_newline:
                continue
            if is_on(node):
                on_seen = True
                groups.append([])
            elif on_seen and is_and_or(node):
                groups.append([])
            groups[-1].append(node)

        groups = [g for g in groups if g]
        if not groups:
            return [line]
        groups[0] = [keyword_node] + groups[0]

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

        # standalone/multiline comments render *before* a Line's own content,
        # so they belong on the first split-off group (matching their
        # original position, ahead of the whole join); trailing inline
        # comments render after a Line's content, so they belong on the
        # last group. Misplacing a standalone comment onto a later group
        # changes its printed position relative to the join/table-ref line,
        # which both looks wrong and breaks idempotency (the comment's new
        # position can change how the next pass merges things).
        for comment in line.comments:
            if comment.is_standalone or comment.is_multiline:
                new_lines[0].comments.append(comment)
            else:
                new_lines[-1].comments.append(comment)

        return new_lines

    def _box_cte_bodies(self, lines: List[Line]) -> List[Line]:
        """
        Every CTE's body gets a blank line immediately after its opening
        "as (" and immediately before its closing ")" (house style
        stories 5-6), regardless of whether the body is one line (a
        trivial import CTE) or many. The closing ")" (or "),") is already
        glued onto a single Line by the merger's existing stubborn-merge
        behavior -- nothing to do there. Also inserts a blank line after
        a CTE's closing line when more content follows (e.g. the next
        CTE's name), so CTE boundaries are unambiguous; the separate
        blank-line-before-next-major-clause rule in _insert_blank_lines
        already covers the case where the with-clause ends and the main
        query's own first clause follows.
        """
        node_manager = NodeManager(self.mode.dialect.case_sensitive_names)

        def blank_line_after(prev_line: Line) -> Line:
            blank_line = Line(previous_node=prev_line.nodes[-1] if prev_line.nodes else None)
            node_manager.append_newline(blank_line)
            return blank_line

        new_lines: List[Line] = []
        for i, line in enumerate(lines):
            if (
                line.closes_cte_body
                and not line.formatting_disabled
                and new_lines
                and not new_lines[-1].is_blank_line
            ):
                new_lines.append(blank_line_after(new_lines[-1]))

            new_lines.append(line)

            next_line = lines[i + 1] if i + 1 < len(lines) else None
            if (
                (line.opens_cte_body or line.closes_cte_body)
                and not line.formatting_disabled
                and next_line is not None
                and not next_line.is_blank_line
            ):
                new_lines.append(blank_line_after(line))

        return new_lines

    def _box_subqueries(self, lines: List[Line]) -> List[Line]:
        """
        Boxes a subquery's parens -- a derived table in from/join, an
        `in (...)`/`exists (...)` subquery, or a bare scalar subquery --
        with the universal multi-line-construct blank-line rule: a blank
        line immediately after the opening "(" and immediately before the
        closing ")" (house style story 19, 25, 33), with one documented
        exception: a bare scalar-subquery wrapper (one with no `in`/
        `exists`/`from`/join keyword directly before its open paren) gets
        no blank line after its opening "(", only before its closing ")"
        (story 32). A CTE's own open paren is excluded here, since
        `_box_cte_bodies` already handles that case (and has no
        bare-subquery exception to worry about).

        Only parens that are genuinely multi-line are boxed: a subquery
        the merger already collapsed onto a single Line (e.g.
        `(select 1)`) has nothing to box, and is skipped naturally since
        its open paren isn't the last content Node on its Line.
        """
        insert_blank_after: set = set()
        insert_blank_before: set = set()

        for i, line in enumerate(lines):
            if line.formatting_disabled or not line.nodes:
                continue
            content_nodes = [n for n in line.nodes if not n.is_newline]
            if not content_nodes:
                continue
            open_node = content_nodes[-1]
            if (
                open_node.token.type is not TokenType.BRACKET_OPEN
                or open_node.value != "("
            ):
                continue
            # CTE bodies (including ones _box_cte_bodies' stricter
            # name-based detection misses, e.g. a jinja-templated CTE
            # name) are out of scope here -- any paren opened directly
            # inside a with-clause's bracket is a CTE body, not a
            # derived table/scalar/in/exists subquery, and stays owned
            # by _box_cte_bodies.
            if open_node.is_cte_open_paren:
                continue
            enclosing = open_node.open_brackets[-1] if open_node.open_brackets else None
            if (
                enclosing is not None
                and enclosing.is_unterm_keyword
                and enclosing.value.split(" ", 1)[0] == "with"
            ):
                continue

            next_line = next(
                (
                    later
                    for later in lines[i + 1 :]
                    if later.nodes and not later.is_blank_line
                ),
                None,
            )
            if next_line is None:
                continue
            first_content = next(
                (n for n in next_line.nodes if not n.is_newline), None
            )
            if first_content is None or not first_content.is_unterm_keyword:
                continue
            if first_content.value.split(" ", 1)[0] not in ("select", "with"):
                continue  # a plain grouping/function-call paren, not a subquery

            close_idx = self._find_matching_close_idx(lines, i, open_node)
            if close_idx is None or close_idx <= i + 1:
                continue

            if not self._is_bare_scalar_subquery_paren(open_node):
                insert_blank_after.add(i)
            insert_blank_before.add(close_idx)

        if not insert_blank_after and not insert_blank_before:
            return lines

        node_manager = NodeManager(self.mode.dialect.case_sensitive_names)
        new_lines: List[Line] = []
        for i, line in enumerate(lines):
            if (
                i in insert_blank_before
                and new_lines
                and not new_lines[-1].is_blank_line
            ):
                blank_line = Line(previous_node=line.previous_node)
                node_manager.append_newline(blank_line)
                new_lines.append(blank_line)
            new_lines.append(line)
            if (
                i in insert_blank_after
                and i + 1 < len(lines)
                and not lines[i + 1].is_blank_line
            ):
                blank_line = Line(
                    previous_node=line.nodes[-1] if line.nodes else line.previous_node
                )
                node_manager.append_newline(blank_line)
                new_lines.append(blank_line)
        return new_lines

    @staticmethod
    def _is_bare_scalar_subquery_paren(open_node: Node) -> bool:
        """
        True for a subquery's opening "(" that isn't directly preceded by
        `in`/`exists` (a predicate subquery) or `from`/a join keyword (a
        derived table) -- i.e. the bare `(...)` scalar-subquery wrapper
        that's the one exception to the universal open-paren blank-line
        rule (house style story 32).
        """
        prev = get_previous_node(open_node.previous_node)
        if prev is None:
            return True
        if prev.token.type is TokenType.WORD_OPERATOR:
            if prev.value.split(" ")[-1] in ("in", "exists"):
                return False
        elif prev.token.type is TokenType.UNTERM_KEYWORD:
            first_word = prev.value.split(" ", 1)[0]
            if first_word == "from" or prev.value.endswith("join"):
                return False
        return True

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
            starts_clause_after_config = (
                line.is_with_clause_start or line.starts_new_major_clause
            ) and bool(new_lines) and new_lines[-1].is_dbt_config_block
            if (
                (line.starts_new_major_clause or starts_clause_after_config)
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

    def _box_window_functions(self, lines: List[Line]) -> List[Line]:
        """
        Boxes each non-trivial window function (an over (...) with a
        partition by/order by/frame-clause sub-clause) with a blank
        line, per the house style's universal multi-line-construct rule
        -- except over (...) itself is never blank-line-boxed on the
        inside (that's enforced upstream by the merger; see
        Node.is_window_subclause_start).

        - If the window function is wrapped inside another function
          call's parens (e.g. coalesce(sum(a) over (...), 0)), the blank
          line goes *inside* that outer call's parens, same as any other
          multi-line construct wrapped in a call (story 25).
        - If it's a bare item in a select list on its own, the blank
          line goes *around* it instead (story 28), since there's no
          outer bracket to box and over (...) can't be boxed on the
          inside.
        - Anywhere else (e.g. a window-function predicate in a qualify
          clause), it's left alone -- out of scope for this rule.
        """
        node_line_idx = {
            id(node): i for i, line in enumerate(lines) for node in line.nodes
        }

        insert_blank_before: set = set()
        insert_blank_after: set = set()
        seen_over_parens: set = set()

        for line in lines:
            for node in line.nodes:
                if not node.is_window_subclause_start:
                    continue
                if line.formatting_disabled or node.formatting_disabled:
                    continue
                over_paren = node.open_brackets[-1]
                if id(over_paren) in seen_over_parens:
                    continue
                seen_over_parens.add(id(over_paren))

                open_idx = node_line_idx.get(id(over_paren))
                if open_idx is None:
                    continue
                close_idx = self._find_matching_close_idx(
                    lines, open_idx, over_paren
                )
                if close_idx is None:
                    continue

                outer = (
                    over_paren.open_brackets[-1] if over_paren.open_brackets else None
                )
                if outer is None:
                    continue
                elif self._is_function_call_open_paren(outer):
                    # story 25: box inside the outer call's parens
                    outer_open_idx = node_line_idx.get(id(outer))
                    if outer_open_idx is None:
                        continue
                    outer_close_idx = self._find_matching_close_idx(
                        lines, outer_open_idx, outer
                    )
                    insert_blank_after.add(outer_open_idx)
                    if outer_close_idx is not None:
                        insert_blank_before.add(outer_close_idx)
                elif (
                    outer.is_unterm_keyword
                    and outer.value.split(" ", 1)[0] == "select"
                ):
                    # story 28: box around the bare select-list item
                    insert_blank_before.add(open_idx)
                    insert_blank_after.add(close_idx)
                # else: out of scope (e.g. a qualify predicate) -- leave as-is

        if not insert_blank_before and not insert_blank_after:
            return lines

        node_manager = NodeManager(self.mode.dialect.case_sensitive_names)
        new_lines: List[Line] = []
        for i, line in enumerate(lines):
            if (
                i in insert_blank_before
                and new_lines
                and not new_lines[-1].is_blank_line
            ):
                blank_line = Line(previous_node=line.previous_node)
                node_manager.append_newline(blank_line)
                new_lines.append(blank_line)
            new_lines.append(line)
            if (
                i in insert_blank_after
                and i + 1 < len(lines)
                and not lines[i + 1].is_blank_line
            ):
                blank_line = Line(
                    previous_node=line.nodes[-1] if line.nodes else line.previous_node
                )
                node_manager.append_newline(blank_line)
                new_lines.append(blank_line)
        return new_lines

    @staticmethod
    def _opening_bracket_closed_by(node: Node) -> Optional[Node]:
        """
        Given a closing bracket Node, returns the opening bracket Node
        that it closes (whether or not any content lies between them).
        Returns None if node isn't a closing bracket.
        """
        if not node.is_closing_bracket:
            return None
        prev = node.previous_node
        while prev is not None and prev.is_newline:
            prev = prev.previous_node
        if prev is None:
            return None
        if prev.is_opening_bracket:
            return prev
        if not prev.open_brackets:
            return None
        opening = prev.open_brackets[-1]
        if opening.is_unterm_keyword:
            # the closing bracket pops both the inner unterm keyword
            # (e.g. partition by/where) *and* the bracket it's nested
            # in -- see NodeManager.open_brackets -- so the bracket we
            # actually care about is one level further out
            if len(prev.open_brackets) < 2:
                return None
            opening = prev.open_brackets[-2]
        return opening

    @classmethod
    def _find_matching_close_idx(
        cls, lines: List[Line], open_idx: int, opening_node: Node
    ) -> Optional[int]:
        for j in range(open_idx, len(lines)):
            for node in lines[j].nodes:
                if cls._opening_bracket_closed_by(node) is opening_node:
                    return j
        return None

    @staticmethod
    def _is_function_call_open_paren(node: Node) -> bool:
        if node.token.type is not TokenType.BRACKET_OPEN:
            return False
        prev_token, _ = get_previous_token(node.previous_node)
        return prev_token is not None and prev_token.type in (
            TokenType.NAME,
            TokenType.QUOTED_NAME,
        )

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
            self._remove_semicolons,
            self._force_split_multi_item_clauses,
            self._force_split_join_on_clauses,
            self._box_cte_bodies,
            self._box_subqueries,
            self._insert_blank_lines,
            self._box_window_functions,
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
