from dataclasses import dataclass
from typing import Callable, List, Optional

from sqlfmt.jinjafmt import JinjaFormatter
from sqlfmt.line import Line
from sqlfmt.merger import LineMerger
from sqlfmt.mode import Mode
from sqlfmt.node import FORCE_SPLIT_CLAUSE_KEYWORDS, Node, get_previous_token
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

    def _fix_case_then_depth(self, lines: List[Line]) -> List[Line]:
        """
        Node depth is computed purely from bracket/keyword nesting, which
        naturally puts a case expression's `then` keyword at the same
        depth as its `when` -- but house style indents a `then` that
        doesn't merge onto the `when`/and-or line (because the merged
        line would be too long) one level deeper, aligned with the when
        condition / stacked and/or lines, rather than back out to
        `when`'s own indent.

        This bumps the first node of every Line that's either such an
        isolated `then`, or nested *underneath* one (e.g. a nested case
        expression that's the `then` value) -- the latter needs the same
        +1 to stay one level deeper than its now-bumped `then`, rather
        than colliding with it. A Line nested under N isolated `then`s
        (nested cases each landing in this situation) gets bumped by N,
        so depth keeps increasing correctly at each level.
        """
        isolated_then_ids = {
            id(line.nodes[0])
            for line in lines
            if line.nodes
            and line.nodes[0].is_unterm_keyword
            and line.nodes[0].value == "then"
        }
        if not isolated_then_ids:
            return lines

        for line in lines:
            if not line.nodes:
                continue
            first = line.nodes[0]
            bump = sum(1 for b in first.open_brackets if id(b) in isolated_then_ids)
            if id(first) in isolated_then_ids:
                bump += 1
            if bump:
                first.open_brackets = first.open_brackets + [first] * bump
        return lines

    def _box_function_wrapped_constructs(self, lines: List[Line]) -> List[Line]:
        """
        Story 25: a multi-line construct wrapped inside a function call's
        parentheses (e.g. `sum(case ... end)`) gets a blank line
        immediately after the function's opening `(` and immediately
        before its closing `)`, same as the universal multi-line-wrap box
        rule -- but only when the function call's parens actually span
        more than one Line after merging (if the whole thing collapses
        to one line, there's nothing to box).

        Only case expressions are recognized as boxable constructs here;
        window functions and subqueries are the same "construct wrapped
        in a function call" shape and should extend
        _is_boxable_construct_start rather than duplicating this pass.
        """
        boxable_ids = {
            id(node.open_brackets[-1])
            for node in self._iter_nodes(lines)
            if self._is_boxable_construct_start(node)
            and node.open_brackets
            and node.open_brackets[-1].token.type is TokenType.BRACKET_OPEN
            and node.open_brackets[-1].value == "("
            and self._opens_function_call(node.open_brackets[-1])
        }
        if not boxable_ids:
            return lines

        node_manager = NodeManager(self.mode.dialect.case_sensitive_names)
        new_lines: List[Line] = []
        for line in lines:
            if (
                line.nodes
                and new_lines
                and not new_lines[-1].is_blank_line
                and self._closes_boxable_bracket(line, boxable_ids)
            ):
                blank_line = Line(previous_node=line.previous_node)
                node_manager.append_newline(blank_line)
                new_lines.append(blank_line)

            new_lines.append(line)

            if (
                line.nodes
                and line.opens_new_bracket
                and id(line.nodes[-1].open_brackets[-1]) in boxable_ids
            ):
                blank_line = Line(previous_node=line.nodes[-1])
                node_manager.append_newline(blank_line)
                new_lines.append(blank_line)

        return new_lines

    @staticmethod
    def _iter_nodes(lines: List[Line]) -> List[Node]:
        return [node for line in lines for node in line.nodes if not node.is_newline]

    @staticmethod
    def _is_boxable_construct_start(node: Node) -> bool:
        """
        True for a node that starts a construct story 25's box rule
        applies to. Only case expressions are in scope for this ticket;
        window functions/subqueries extend this predicate in their own
        tickets rather than adding a parallel mechanism.
        """
        return node.token.type is TokenType.STATEMENT_START and node.value == "case"

    @staticmethod
    def _opens_function_call(paren_node: Node) -> bool:
        """
        True if paren_node is a "(" immediately preceded by a name, i.e.
        a function call's opening paren, as opposed to a bare scalar
        subquery wrapper (story 32's exception) or any other grouping
        paren.
        """
        prev_token, _ = get_previous_token(paren_node.previous_node)
        return prev_token is not None and prev_token.type in (
            TokenType.NAME,
            TokenType.QUOTED_NAME,
        )

    @staticmethod
    def _closes_boxable_bracket(line: Line, boxable_ids: set) -> bool:
        if not (line.previous_node and line.previous_node.open_brackets and line.nodes):
            return False
        explicit_brackets = [
            b for b in line.previous_node.open_brackets if b.is_opening_bracket
        ]
        if not explicit_brackets:
            return False
        last = explicit_brackets[-1]
        if last in line.nodes[-1].open_brackets:
            return False
        return id(last) in boxable_ids

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
            self._fix_case_then_depth,
            self._box_function_wrapped_constructs,
            self._box_cte_bodies,
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
