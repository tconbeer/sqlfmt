from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from sqlfmt.token import Token, TokenType


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
            return not (
                prev_token.type
                in (TokenType.UNTERM_KEYWORD, TokenType.COMMA, TokenType.DOT)
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
    def is_newline(self) -> bool:
        return self.token.type is TokenType.NEWLINE

    @property
    def is_multiline_jinja(self) -> bool:
        if self.token.type.is_jinja and "\n" in self.value:
            return True
        else:
            return False
