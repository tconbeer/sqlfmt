from dataclasses import dataclass
from typing import Callable, List, Optional

from sqlfmt.jinjafmt import JinjaFormatter
from sqlfmt.line import Line
from sqlfmt.merger import LineMerger
from sqlfmt.mode import Mode
from sqlfmt.node import (
    COMMA_SEPARATED_CLAUSE_KEYWORDS,
    FORCE_SPLIT_CLAUSE_KEYWORDS,
    Node,
    _is_over_open_paren,
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

    def _merge_simple_when_then(self, lines: List[Line]) -> List[Line]:
        """
        Stories 21/22: whether a `when ... then ...` breaks onto two
        lines must be judged per when-clause, independently of its
        sibling whens in the same case. The generic recursive merger
        segments a case's body by depth, and once any sibling when/
        then pair in the case has been forced multi-line (story 22's
        and/or rule, or -- once case expressions always break multi-
        line per story 20 -- just by virtue of being in a case at all),
        every when/then pair in that case ends up isolated into its
        own single-Line segment by that depth-based segmentation, with
        no further chance to recombine.

        This re-merges any `when ...`/`then ...` pair still split onto
        two Lines, whenever the when condition has no and/or (story 22
        already keeps those split) and the combined line fits within
        the line-length limit (story 21). A `then` Line that's bare
        (nothing merged onto it yet, e.g. because its own value is a
        multi-line nested construct) is left alone -- that's not this
        bug, and must stay split.
        """
        node_manager = NodeManager(self.mode.dialect.case_sensitive_names)
        new_lines: List[Line] = []
        skip_next = False
        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue
            next_line = lines[i + 1] if i + 1 < len(lines) else None
            if (
                next_line is not None
                and not next_line.is_blank_line
                and not line.formatting_disabled
                and not next_line.formatting_disabled
                and line.nodes
                and line.nodes[0].is_unterm_keyword
                and line.nodes[0].value == "when"
                and not any(n.is_case_when_condition_separator for n in line.nodes)
                and next_line.nodes
                and next_line.nodes[0].is_unterm_keyword
                and next_line.nodes[0].value == "then"
                and len([n for n in next_line.nodes if not n.is_newline]) > 1
            ):
                content_nodes = [n for n in line.nodes if not n.is_newline] + [
                    n for n in next_line.nodes if not n.is_newline
                ]
                merged_line = Line.from_nodes(
                    previous_node=line.previous_node,
                    nodes=content_nodes,
                    comments=line.comments + next_line.comments,
                )
                node_manager.append_newline(merged_line)
                if not merged_line.is_too_long(self.mode.line_length):
                    new_lines.append(merged_line)
                    skip_next = True
                    continue
            new_lines.append(line)
        return new_lines

    def _merge_trivial_select_star_from(self, lines: List[Line]) -> List[Line]:
        """
        Stories 2/3: a trivial "select *" / "from <single source>" pair
        collapses onto one line when it's a branch of a top-level union
        (etc.) or the file's outermost final select -- the same
        triviality rule the generic merger already applies to a trivial
        import CTE's body (LineMerger._is_trivial_select_star_body), but
        those two contexts never reach the merger as a standalone
        [select_line, from_line] pair: segmentation splits every
        top-level line into its own segment (they're all the same
        depth), so the merger only ever tries to merge each of
        select/from in isolation. This re-glues them after the fact,
        whenever both lines are otherwise untouched (nothing else
        already merged onto either of them).
        """
        from sqlfmt.merger import LineMerger

        node_manager = NodeManager(self.mode.dialect.case_sensitive_names)
        new_lines: List[Line] = []
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]
            # a pre-existing blank line between "select *" and "from x" (e.g.
            # from source text written in the old, pre-collapse style) must
            # not block the merge -- skip over it (and drop it) the same as
            # if it weren't there.
            j = i + 1
            while j < n and lines[j].is_blank_line:
                j += 1
            next_line = lines[j] if j < n else None
            if (
                next_line is not None
                and not line.formatting_disabled
                and not next_line.formatting_disabled
                and line.nodes
                and line.nodes[0].is_major_clause_keyword
                and line.nodes[0].value == "select"
                and next_line.nodes
                and next_line.nodes[0].is_major_clause_keyword
                and next_line.nodes[0].value == "from"
                and LineMerger._is_trivial_select_star_body([line, next_line])
                and not self._followed_by_same_statement_clause(lines, j + 1)
            ):
                merged_nodes = [n for n in line.nodes if not n.is_newline] + [
                    n for n in next_line.nodes if not n.is_newline
                ]
                merged_line = Line.from_nodes(
                    previous_node=line.previous_node,
                    nodes=merged_nodes,
                    comments=line.comments + next_line.comments,
                )
                node_manager.append_newline(merged_line)
                if not merged_line.is_too_long(self.mode.line_length):
                    new_lines.append(merged_line)
                    i = j + 1
                    continue
            new_lines.append(line)
            i += 1
        return new_lines

    @staticmethod
    def _followed_by_same_statement_clause(lines: List[Line], start: int) -> bool:
        """
        True iff the next non-blank Line at or after `start` continues
        the *same* select statement with anything else -- another
        top-level clause (where/group by/having/order by/qualify/
        limit), a join, or any other table-expression modifier (e.g.
        Spark's `lateral view`) -- which means the "select */from x"
        pair ahead of it isn't actually trivial (it's not "literally
        nothing else", per stories 2/3) and must not collapse onto one
        line. A `union`/`intersect`/`except` at the same depth, a Line
        that closes an enclosing bracket (the from's CTE/derived-table
        paren), or end-of-file don't count -- those end the statement
        rather than extending it.
        """
        for later in lines[start:]:
            if later.is_blank_line:
                continue
            if not later.nodes:
                continue
            if later.nodes[0].is_set_operator or later.closes_cte_body:
                return False
            if later.closes_bracket_from_previous_line:
                return False
            return True
        return False

    def _merge_single_condition_clause_keyword(self, lines: List[Line]) -> List[Line]:
        """
        Story 11: a single-condition where/having clause stays on the
        same line as the keyword, even when that one condition's own
        right-hand side is a multi-line subquery (e.g. `where
        customer_id in (select ...)`). The generic merger can't glue
        the keyword onto the condition in one pass in that case --
        the subquery's own content makes the whole clause too long to
        merge as a single unit, so the merger leaves the keyword as
        its own bare Line, followed by the (unmerged) first Line of
        the condition. This re-glues the two back together whenever
        the clause has exactly one condition (no and/or at the
        keyword's child depth -- a multi-condition clause is correctly
        left split by the merger/_force_split_multi_item_clauses,
        per story 12's stacking rule, and must not be touched here).
        """
        new_lines: List[Line] = []
        skip_next = False
        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue
            merged = self._maybe_glue_clause_keyword(lines, i)
            if merged is not None:
                self._dedent_glued_condition_subquery(lines, i, merged)
                new_lines.append(merged)
                skip_next = True
            else:
                new_lines.append(line)
        return new_lines

    def _maybe_glue_clause_keyword(self, lines: List[Line], i: int) -> Optional[Line]:
        line = lines[i]
        next_line = lines[i + 1] if i + 1 < len(lines) else None
        if next_line is None or next_line.is_blank_line or line.formatting_disabled:
            return None
        if not line.nodes or not line.nodes[0].is_unterm_keyword:
            return None

        keyword_node = line.nodes[0]
        keyword = keyword_node.value.split(" ", 1)[0]
        if keyword not in ("where", "having"):
            return None
        # a bare keyword Line has nothing but the keyword itself and a
        # trailing newline -- if the merger already attached content,
        # there's nothing for this pass to do.
        content_nodes = [n for n in line.nodes if not n.is_newline]
        if len(content_nodes) != 1:
            return None

        if not self._is_single_condition_clause(lines, i + 1, keyword_node):
            return None

        merged_nodes = content_nodes + [n for n in next_line.nodes if not n.is_newline]
        merged_line = Line.from_nodes(
            previous_node=line.previous_node,
            nodes=merged_nodes,
            comments=line.comments + next_line.comments,
        )
        node_manager = NodeManager(self.mode.dialect.case_sensitive_names)
        node_manager.append_newline(merged_line)
        if merged_line.is_too_long(self.mode.line_length):
            return None
        return merged_line

    def _dedent_glued_condition_subquery(
        self, lines: List[Line], i: int, merged_line: Line
    ) -> None:
        """
        After _maybe_glue_clause_keyword folds a where/having keyword
        onto its single condition's Line, the keyword no longer
        occupies its own indent level -- the condition's subquery (if
        it ends in an open paren, e.g. `in (`/`exists (`) takes over
        the visual nesting from there, per story 11. The subquery's
        contents and closing paren were parsed one level deeper than
        that (as children of the keyword's own pseudo-bracket, which
        used to get its own printed line), so this strips the keyword
        node out of their open_brackets to shift them back in by that
        one level, mutating the shared Node objects in place (same
        approach as _fix_case_then_depth's depth bump, just shrinking
        instead of growing).
        """
        keyword_node = merged_line.nodes[0]
        content_nodes = [n for n in merged_line.nodes if not n.is_newline]
        if not content_nodes:
            return
        open_node = content_nodes[-1]
        if open_node.token.type is not TokenType.BRACKET_OPEN:
            return
        close_idx = self._find_matching_close_idx(lines, i + 1, open_node)
        if close_idx is None:
            return
        for later_line in lines[i + 1 : close_idx + 1]:
            for node in later_line.nodes:
                if keyword_node in node.open_brackets:
                    node.open_brackets = [
                        b for b in node.open_brackets if b is not keyword_node
                    ]

    @staticmethod
    def _is_single_condition_clause(
        lines: List[Line], start: int, keyword_node: Node
    ) -> bool:
        """
        True iff the where/having clause starting with keyword_node has
        exactly one and/or-free condition -- scanning forward from
        `start` through the clause's own scope (any Line still nested
        at or beneath the keyword's child depth) for a boolean and/or
        at the keyword's immediate child depth, which would mean this
        is a multi-condition clause that must stay split (story 12).
        """
        child_depth = (keyword_node.depth[0] + 1, keyword_node.depth[1])
        for line in lines[start:]:
            if not line.nodes:
                continue
            if line.depth[0] < child_depth[0]:
                break
            for node in line.nodes:
                if node.is_newline:
                    continue
                if (
                    node.depth == child_depth
                    and node.is_boolean_operator
                    and node.value in ("and", "or")
                    and not node.is_the_and_after_the_between_operator
                ):
                    return False
        return True

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
        is_comma_separated = keyword in COMMA_SEPARATED_CLAUSE_KEYWORDS

        def is_item_separator(node: Node) -> bool:
            if node.depth != child_depth:
                return False
            if is_comma_separated:
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
            if is_comma_separated and is_item_separator(node):
                # trailing comma stays with the item it follows
                groups[-1].append(node)
                groups.append([])
                continue
            if not is_comma_separated and is_item_separator(node):
                # and/or leads the next item's line
                groups.append([])
            groups[-1].append(node)

        groups = [g for g in groups if g]
        if not groups:
            return [line]

        # story 13's extension to select: a multi-column select list always
        # breaks one column per line -- but unlike group by/where/having
        # (whose keyword glues onto the first item), select's keyword
        # stands alone on its own line, with every column (including the
        # first) indented below it, matching the general
        # keyword-then-indented-items shape select already uses whenever
        # the merger can't fit the whole list on one line.
        if keyword == "select":
            if len(groups) <= 1:
                return [line]
            item_groups = groups
            keyword_only = True
        else:
            groups[0] = [keyword_node] + groups[0]
            if len(groups) <= 1:
                return [line]
            item_groups = groups
            keyword_only = False

        node_manager = NodeManager(self.mode.dialect.case_sensitive_names)
        new_lines: List[Line] = []
        prev_node = line.previous_node
        if keyword_only:
            keyword_line = Line.from_nodes(
                previous_node=prev_node, nodes=[keyword_node], comments=[]
            )
            node_manager.append_newline(keyword_line)
            new_lines.append(keyword_line)
            prev_node = keyword_line.nodes[-1]
        for group in item_groups:
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

        Case expressions and window functions (via their `over (...)`
        open paren) are recognized as boxable constructs here; any
        other construct wrapped in a function call should likewise
        extend _is_boxable_construct_start rather than duplicating this
        pass. A bare, non-wrapped window function in a select list
        (story 28) has no enclosing function call to box, so that case
        is handled separately by _box_window_functions.
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
        applies to: a case expression's `case`, or a window function's
        `over (...)` open paren. Both shapes are the same "construct
        wrapped in a function call" case -- node.open_brackets[-1] is
        the enclosing call's paren, which the caller boxes. Any future
        boxable construct should extend this predicate rather than
        adding a parallel mechanism (see ticket #7's postmortem).
        """
        if node.token.type is TokenType.STATEMENT_START and node.value == "case":
            return True
        return node.token.type is TokenType.BRACKET_OPEN and _is_over_open_paren(node)

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
            blank_line = Line(
                previous_node=prev_line.nodes[-1] if prev_line.nodes else None
            )
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
            first_content = next((n for n in next_line.nodes if not n.is_newline), None)
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

        return self._splice_blank_lines(lines, insert_blank_before, insert_blank_after)

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
                (line.is_with_clause_start or line.starts_new_major_clause)
                and bool(new_lines)
                and new_lines[-1].is_dbt_config_block
            )
            # story 4/8: a blank line follows "with" before the first CTE's
            # name, same as the blank line after a dbt config() block --
            # the CTE name itself isn't a major clause keyword, so this
            # needs its own trigger here rather than reusing
            # starts_new_major_clause.
            starts_after_with = bool(new_lines) and new_lines[-1].is_with_clause_start
            if (
                (
                    line.starts_new_major_clause
                    or starts_clause_after_config
                    or starts_after_with
                )
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
        Boxes a bare, non-wrapped window function that's a standalone
        item in a select list (story 28) with a blank line above and
        below -- the one window-function boxing shape that isn't
        already covered by the general "construct wrapped in a
        function call" rule (_box_function_wrapped_constructs, which
        _is_boxable_construct_start now also recognizes over (...)
        starts for). over (...) itself is never blank-line-boxed on the
        inside (that's enforced upstream by the merger; see
        Node.is_window_subclause_start) -- this only adds blank lines
        *around* the whole construct, and only when there's no
        enclosing function call to box instead.
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

                outer = (
                    over_paren.open_brackets[-1] if over_paren.open_brackets else None
                )
                if not (
                    outer is not None
                    and outer.is_unterm_keyword
                    and outer.value.split(" ", 1)[0] == "select"
                ):
                    # wrapped in a function call: _box_function_wrapped_constructs
                    # already handles it; anything else (e.g. a qualify
                    # predicate) is out of scope for this rule
                    continue

                open_idx = node_line_idx.get(id(over_paren))
                if open_idx is None:
                    continue
                close_idx = self._find_matching_close_idx(lines, open_idx, over_paren)
                if close_idx is None:
                    continue

                insert_blank_before.add(open_idx)
                insert_blank_after.add(close_idx)

        return self._splice_blank_lines(lines, insert_blank_before, insert_blank_after)

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

    def _splice_blank_lines(
        self, lines: List[Line], before_idxs: set, after_idxs: set
    ) -> List[Line]:
        """
        Shared helper for passes (subqueries, bare window functions)
        that have already decided, by original line index, which Lines
        need a blank Line spliced in immediately before and/or after
        them. Skips an insertion if a blank Line is already present, so
        each pass stays idempotent.
        """
        if not before_idxs and not after_idxs:
            return lines

        node_manager = NodeManager(self.mode.dialect.case_sensitive_names)
        new_lines: List[Line] = []
        for i, line in enumerate(lines):
            if i in before_idxs and new_lines and not new_lines[-1].is_blank_line:
                blank_line = Line(previous_node=line.previous_node)
                node_manager.append_newline(blank_line)
                new_lines.append(blank_line)
            new_lines.append(line)
            if (
                i in after_idxs
                and i + 1 < len(lines)
                and not lines[i + 1].is_blank_line
            ):
                blank_line = Line(
                    previous_node=line.nodes[-1] if line.nodes else line.previous_node
                )
                node_manager.append_newline(blank_line)
                new_lines.append(blank_line)
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
            self._merge_trivial_select_star_from,
            self._remove_semicolons,
            self._merge_simple_when_then,
            self._merge_single_condition_clause_keyword,
            self._force_split_multi_item_clauses,
            self._force_split_join_on_clauses,
            self._fix_case_then_depth,
            self._box_function_wrapped_constructs,
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
