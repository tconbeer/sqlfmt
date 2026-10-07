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


def get_previous_node(prev_node: Optional["Node"]) -> Optional["Node"]:
    """
    Returns prev_node, unless prev_node is a newline or jinja statement
    (nodes that don't set sql context), in which case it recurses to find
    the nearest preceding Node that does
    """
    if prev_node is None:
        return None
    if prev_node.token.type.does_not_set_prev_sql_context:
        return get_previous_node(prev_node.previous_node)
    return prev_node


def _is_over_open_paren(node: "Node") -> bool:
    """
    True if node is the opening "(" of a window function's over (...)
    (as opposed to any other bracket, like a plain function call or
    "within group (...)").
    """
    if node.token.type is not TokenType.BRACKET_OPEN:
        return False
    prev_token, _ = get_previous_token(node.previous_node)
    if prev_token is None or prev_token.type is not TokenType.WORD_OPERATOR:
        return False
    return " ".join(prev_token.token.lower().split()) == "over"


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
    def is_semicolon(self) -> bool:
        return self.token.type is TokenType.SEMICOLON

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
    def is_window_subclause_start(self) -> bool:
        """
        True for the first Node (partition by/order by/a frame clause's
        rows|range|groups keyword) of a sub-clause nested directly inside
        a window function's over (...). Used to always force each
        sub-clause onto its own line (house style story 26) -- unlike
        "within group (order by ...)", which isn't a window function and
        isn't in scope for this rule.
        """
        if not self.is_unterm_keyword:
            return False
        if not self.open_brackets:
            return False
        return _is_over_open_paren(self.open_brackets[-1])

    @property
    def closes_non_trivial_over_clause(self) -> bool:
        """
        True for the closing ")" of a window function's over (...) that
        has at least one sub-clause inside it (i.e. isn't the trivial
        `over ()`).
        """
        if not self.is_closing_bracket:
            return False
        prev = self.previous_node
        while prev is not None and prev.is_newline:
            prev = prev.previous_node
        if prev is None:
            return False
        if prev.is_opening_bracket:
            return _is_over_open_paren(prev)
        if not prev.open_brackets:
            return False
        opening = prev.open_brackets[-1]
        if opening.is_unterm_keyword:
            # the closing bracket pops both the sub-clause keyword (e.g.
            # partition by/order by) *and* the bracket it's nested in --
            # see NodeManager.open_brackets -- so the bracket we actually
            # care about is one level further out
            if len(prev.open_brackets) < 2:
                return False
            opening = prev.open_brackets[-2]
        return _is_over_open_paren(opening)

    @property
    def is_cte_open_paren(self) -> bool:
        """
        True for a BRACKET_OPEN "(" node that opens the body of a CTE --
        i.e., that immediately follows the "as" in a with-clause's
        "<name> as (" pattern. Used to box CTE bodies with blank lines
        after the opening paren and before the closing paren (house style
        stories 4-6), regardless of whether the body is trivial (one line)
        or not.
        """
        if self.token.type is not TokenType.BRACKET_OPEN or self.value != "(":
            return False
        as_node = get_previous_node(self.previous_node)
        if (
            as_node is None
            or as_node.token.type is not TokenType.WORD_OPERATOR
            or as_node.value != "as"
        ):
            return False
        name_node = get_previous_node(as_node.previous_node)
        if name_node is None or name_node.token.type not in (
            TokenType.NAME,
            TokenType.QUOTED_NAME,
        ):
            return False
        if not self.open_brackets:
            return False
        enclosing = self.open_brackets[-1]
        return (
            enclosing.is_unterm_keyword
            and enclosing.value.split(" ", 1)[0] == "with"
        )

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
