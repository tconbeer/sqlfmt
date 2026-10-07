from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from sqlfmt.tokens import Token, TokenType

# UNTERM_KEYWORD values (by first word) that start a top-level clause of a
# select statement, as opposed to other UNTERM_KEYWORDs (joins, with, when/
# then/else, partition by, ...) that are handled by other formatting rules.
# This set is intentionally the only thing that need grow as more clauses
# gain house-style treatment -- the blank-line-insertion machinery itself
# (Line.starts_new_major_clause) is generic over whatever is listed here.
MAJOR_CLAUSE_KEYWORDS = frozenset(
    {"select", "from", "where", "group", "having", "order", "qualify", "limit"}
)

# Clause keywords (by first word) whose items (conditions joined by and/or,
# or columns joined by commas) must always be split one-per-line when there
# is more than one item, regardless of whether the whole clause would fit
# on one line.
FORCE_SPLIT_CLAUSE_KEYWORDS = frozenset({"where", "having", "group"})


def get_previous_token(prev_node: Optional["Node"]) -> Tuple[Optional[Token], bool]:
    """
    Returns the token of prev_node, unless prev_node is a
    newline or jinja statement, in which case it recurses
    """
    if not prev_node:
        return None, False
    t = prev_node.token
    if t.type.does_not_set_prev_sql_context:
        prev, _ = get_previous_token(prev_node.previous_node)
        return prev, True
    else:
        return t, False


@dataclass
class Node:
    """
    A Node wraps a lexed Token, but adds many calculated properties and methods that
    simplify formatting, including:

    previous_node: a reference to the Node that immediately precedes this Node in the
    query

    prefix: the calculated whitespace (0 or 1 spaces) that should precede this Node
    when formatted

    value: the properly-capitalized token contents for the formatted query

    open_brackets and open_jinja_blocks: a list of Nodes that precede this Node that
    refer to open brackets (keywords and parens) or jinja blocks (e.g., {% if foo %})
    that increase the syntax depth (and therefore printed indentation) of this Node

    formatting_disabled: a list of FMT_OFF tokens that precede this node and prevent
    it from being formatted
    """

    token: Token
    previous_node: Optional["Node"]
    prefix: str
    value: str
    open_brackets: List["Node"] = field(default_factory=list)
    open_jinja_blocks: List["Node"] = field(default_factory=list)
    formatting_disabled: List[Token] = field(default_factory=list)

    def __str__(self) -> str:
        """
        Returns the formatted text of this Node
        """
        return f"{self.prefix}{self.value}"

    def __repr__(self) -> str:
        """
        Because of self.previous_node, the default dataclass repr creates
        unusable output
        """

        def simple_node(node: Optional[Node]) -> str:
            return f"Node(token={node.token})" if node else "None"

        prev = simple_node(self.previous_node)
        b = [simple_node(n) for n in self.open_brackets]
        j = [simple_node(n) for n in self.open_jinja_blocks]
        r = (
            f"Node(\n"
            f"\ttoken='{str(self.token)}',\n"
            f"\tprevious_node={prev},\n"
            f"\tdepth={self.depth},\n"
            f"\tprefix='{self.prefix}',\n"
            f"\tvalue='{self.value}',\n"
            f"\topen_brackets={b},\n"
            f"\topen_jinja_blocks={j},\n"
            f"\tformatting_disabled={self.formatting_disabled}\n"
            f")"
        )
        return r

    def __len__(self) -> int:
        """
        The length of this printed Node, including prefix whitespace, after formatting
        """
        return len(str(self))

    @property
    def depth(self) -> Tuple[int, int]:
        """
        A Node's depth is a key characteristic that determines its indentation in the
        formatted query. We use a tuple to track SQL and jinja depth separately, since
        SQL depth can change within jinja blocks
        """
        return (len(self.open_brackets), len(self.open_jinja_blocks))

    @property
    def is_unterm_keyword(self) -> bool:
        """
        True for Nodes representing unterminated SQL keywords, like select, from, where
        """
        return self.token.type is TokenType.UNTERM_KEYWORD

    @property
    def is_comma(self) -> bool:
        return self.token.type is TokenType.COMMA

    @property
    def divides_queries(self) -> bool:
        return self.token.type.divides_queries

    @property
    def is_opening_bracket(self) -> bool:
        return self.token.type.is_opening_bracket

    @property
    def is_bracket_operator(self) -> bool:
        """
        Node is an opening square bracket ("[")
        that follows a token that could be a name.

        Alternatively, node is an open paren ("(")
        that follow an closing angle bracket.
        """
        if self.token.type is not TokenType.BRACKET_OPEN:
            return False

        prev_token, _ = get_previous_token(self.previous_node)
        if not prev_token:
            return False
        elif self.value == "[":
            return prev_token.type in (
                TokenType.NAME,
                TokenType.QUOTED_NAME,
                TokenType.BRACKET_CLOSE,
            )
        # BQ struct literals have parens that follow closing angle
        # brackets
        else:
            return (
                self.value == "("
                and prev_token.type is TokenType.BRACKET_CLOSE
                and ">" in prev_token.token
            )

    @property
    def is_closing_bracket(self) -> bool:
        return self.token.type in (
            TokenType.BRACKET_CLOSE,
            TokenType.STATEMENT_END,
        )

    @property
    def is_opening_jinja_block(self) -> bool:
        return self.token.type in (
            TokenType.JINJA_BLOCK_START,
            TokenType.JINJA_BLOCK_KEYWORD,
        )

    @property
    def is_jinja(self) -> bool:
        return self.token.type.is_jinja

    @property
    def is_closing_jinja_block(self) -> bool:
        return self.token.type is TokenType.JINJA_BLOCK_END

    @property
    def is_jinja_block_keyword(self) -> bool:
        return self.token.type is TokenType.JINJA_BLOCK_KEYWORD

    @property
    def is_jinja_statement(self) -> bool:
        return self.token.type.is_jinja_statement

    @property
    def is_operator(self) -> bool:
        return (
            self.token.type.is_always_operator
            or self.is_multiplication_star
            or self.is_bracket_operator
        )

    @property
    def is_boolean_operator(self) -> bool:
        return self.token.type is TokenType.BOOLEAN_OPERATOR

    @property
    def is_multiplication_star(self) -> bool:
        """
        A lexed TokenType.STAR token can be the "all fields" shorthand or
        the multiplication operator. Returns true iff this Node is a multiplication
        operator
        """
        if self.token.type is not TokenType.STAR:
            return False
        prev_token, _ = get_previous_token(self.previous_node)
        if not prev_token:
            return False
        else:
            return prev_token.type not in (
                TokenType.UNTERM_KEYWORD,
                TokenType.COMMA,
                TokenType.DOT,
            )

    @property
    def is_the_between_operator(self) -> bool:
        """
        True if this node is a WORD_OPERATOR with the value "between"
        """
        return self.token.type is TokenType.WORD_OPERATOR and self.value == "between"

    @property
    def has_preceding_between_operator(self) -> bool:
        """
        True if this node has a preceding "between" operator at the same depth
        """
        prev = (
            self.previous_node.previous_node if self.previous_node is not None else None
        )
        while prev and prev.depth >= self.depth:
            if prev.depth == self.depth and prev.is_the_between_operator:
                return True
            elif prev.depth == self.depth and prev.is_boolean_operator:
                break
            else:
                prev = prev.previous_node
        return False

    @property
    def is_the_and_after_the_between_operator(self) -> bool:
        """
        True if this node is a BOOLEAN_OPERATOR with the value "and" immediately
        following a "between" operator
        """
        if not self.is_boolean_operator or self.value != "and":
            return False
        else:
            return self.has_preceding_between_operator

    @property
    def is_major_clause_keyword(self) -> bool:
        """
        True for UNTERM_KEYWORD nodes that start a top-level clause of a
        select statement (select, from, where, group by, having, order by,
        qualify, limit). Used to insert blank lines between clauses, and
        (for a subset of these) to force always-split formatting of
        multi-item clauses. Deliberately keyed off a value set, not every
        UNTERM_KEYWORD, so it excludes joins, with, when/then/else,
        partition by, etc.
        """
        if not self.is_unterm_keyword:
            return False
        first_word = self.value.split(" ", 1)[0]
        if first_word not in MAJOR_CLAUSE_KEYWORDS:
            return False
        # "order by" is also valid syntax nested inside a window function's
        # over (...) or an ordered-set aggregate's within group (...) --
        # that's not the select statement's own order by clause, so it
        # doesn't count as a major clause (and shouldn't force a blank
        # line / split).
        if first_word == "order" and self._is_nested_in_over_or_within_group:
            return False
        return True

    @property
    def _is_nested_in_over_or_within_group(self) -> bool:
        if not self.open_brackets:
            return False
        parent = self.open_brackets[-1]
        if parent.token.type is not TokenType.BRACKET_OPEN:
            return False
        prev_token, _ = get_previous_token(parent.previous_node)
        if prev_token is None or prev_token.type is not TokenType.WORD_OPERATOR:
            return False
        normalized = " ".join(prev_token.token.lower().split())
        return normalized in ("over", "within group")

    @property
    def is_case_clause_boundary(self) -> bool:
        """
        True for a node that starts a case expression's `case`, `when`,
        or `else` -- the discrete positions house style always renders on
        their own line (story 20), never merged onto whatever precedes
        them (unlike `then`, which may still join the tail of its `when`/
        and-or line when it fits -- see is_case_when_condition_separator
        and the merger guard that uses both of these). `end` doesn't need
        this: it's already a STATEMENT_END/closing bracket, so the
        splitter already always splits before it.
        """
        if self.token.type is TokenType.STATEMENT_START and self.value == "case":
            return True
        return self.is_unterm_keyword and self.value in ("when", "else")

    @property
    def is_case_when_condition_separator(self) -> bool:
        """
        True for a BOOLEAN_OPERATOR (and/or, excluding the "and" after a
        "between" operator) that is a direct child of a case expression's
        `when` keyword -- i.e., part of the when condition itself, not a
        nested sub-expression's own and/or (which stays wherever it
        naturally falls, e.g. inside a parenthesized group).

        House style always breaks a when condition containing and/or onto
        multiple lines, regardless of length, same as where/having and/or
        stacking -- but when/then/else aren't top-level clauses (see
        MAJOR_CLAUSE_KEYWORDS), so this is a parallel, narrower guard used
        by the merger to prevent collapsing across this boundary, rather
        than reusing the clause-level machinery.
        """
        if not (self.is_boolean_operator and self.value in ("and", "or")):
            return False
        if self.is_the_and_after_the_between_operator:
            return False
        if not self.open_brackets:
            return False
        parent = self.open_brackets[-1]
        return parent.is_unterm_keyword and parent.value == "when"

    @property
    def is_set_operator(self) -> bool:
        """
        True for union/union all/intersect/except/minus
        """
        return self.token.type is TokenType.SET_OPERATOR

    @property
    def is_newline(self) -> bool:
        return self.token.type is TokenType.NEWLINE

    @property
    def is_multiline_jinja(self) -> bool:
        if self.token.type.is_jinja and "\n" in self.value:
            return True
        else:
            return False
