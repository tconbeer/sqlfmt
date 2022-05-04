import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from sqlfmt.exception import SqlfmtBracketError
from sqlfmt.token import Token, TokenType

if sys.version_info >= (3, 8):
    from functools import cached_property
else:
    from backports.cached_property import cached_property


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

    formatting_disabled: a boolean indicating that sqlfmt should print the raw token
    instead of the formatted values for this Node
    """

    token: Token
    previous_node: Optional["Node"]
    prefix: str
    value: str
    open_brackets: List["Node"] = field(default_factory=list)
    open_jinja_blocks: List["Node"] = field(default_factory=list)
    formatting_disabled: bool = False

    def __str__(self) -> str:
        """
        Returns the formatted text of this Node
        """
        return self.prefix + self.value

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
        return self.token.type == TokenType.UNTERM_KEYWORD

    @property
    def is_comma(self) -> bool:
        return self.token.type == TokenType.COMMA

    @property
    def is_semicolon(self) -> bool:
        return self.token.type == TokenType.SEMICOLON

    @property
    def is_opening_bracket(self) -> bool:
        return self.token.type in (
            TokenType.BRACKET_OPEN,
            TokenType.STATEMENT_START,
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
        return self.token.type in (
            TokenType.JINJA_EXPRESSION,
            TokenType.JINJA_STATEMENT,
            TokenType.JINJA_BLOCK_START,
            TokenType.JINJA_BLOCK_KEYWORD,
            TokenType.JINJA_BLOCK_END,
        )

    @property
    def is_closing_jinja_block(self) -> bool:
        return self.token.type == TokenType.JINJA_BLOCK_END

    @property
    def is_jinja_block_keyword(self) -> bool:
        return self.token.type == TokenType.JINJA_BLOCK_KEYWORD

    @property
    def is_jinja_statement(self) -> bool:
        return self.token.type in (
            TokenType.JINJA_STATEMENT,
            TokenType.JINJA_BLOCK_START,
            TokenType.JINJA_BLOCK_KEYWORD,
            TokenType.JINJA_BLOCK_END,
        )

    @cached_property
    def is_operator(self) -> bool:
        return (
            self.token.type
            in (
                TokenType.OPERATOR,
                TokenType.WORD_OPERATOR,
                TokenType.AS,
                TokenType.ON,
                TokenType.BOOLEAN_OPERATOR,
                TokenType.SEMICOLON,
            )
            or self.is_multiplication_star
        )

    @property
    def is_boolean_operator(self) -> bool:
        return self.token.type == TokenType.BOOLEAN_OPERATOR

    @property
    def is_multiplication_star(self) -> bool:
        """
        A lexed TokenType.STAR token can be the "all fields" shorthand or
        the multiplication operator. Returns true iff this Node is a multiplication
        operator
        """
        if self.token.type != TokenType.STAR:
            return False
        prev_token, _ = self.previous_token(self.previous_node)
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
        return self.token.type == TokenType.WORD_OPERATOR and self.value == "between"

    @cached_property
    def has_preceding_between_operator(self) -> bool:
        """
        True if this node has a preceding "between" operator at the same depth
        """
        prev = self.previous_node.previous_node if self.previous_node else None
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
    def is_low_priority_merge_operator(self) -> bool:
        return self.token.type in (TokenType.BOOLEAN_OPERATOR, TokenType.ON)

    @property
    def is_newline(self) -> bool:
        return self.token.type == TokenType.NEWLINE

    @cached_property
    def is_multiline(self) -> bool:
        if (
            self.token.type
            in (
                TokenType.DATA,
                TokenType.JINJA_EXPRESSION,
                TokenType.JINJA_STATEMENT,
                TokenType.JINJA_BLOCK_START,
                TokenType.JINJA_BLOCK_END,
                TokenType.JINJA_BLOCK_KEYWORD,
            )
            and "\n" in self.value
        ):
            return True
        else:
            return False

    @classmethod
    def from_token(cls, token: Token, previous_node: Optional["Node"]) -> "Node":
        """
        Create a Node from a Token. For the Node to be properly formatted,
        method call must also include a reference to the previous Node in the
        Query (either on the same or previous Line), unless it is the first
        Node in the Query.

        The Node's depth and whitespace are calculated when it is created
        (this does most of the formatting of the Node). Node values are
        lowercased if they are simple names, keywords, or statements.
        """

        if previous_node is None:
            open_brackets = []
            open_jinja_blocks = []
            formatting_disabled = False
        else:
            open_brackets = previous_node.open_brackets.copy()
            open_jinja_blocks = previous_node.open_jinja_blocks.copy()
            formatting_disabled = previous_node.formatting_disabled

            # add the previous node to the list of open brackets or jinja blocks
            if previous_node.is_unterm_keyword or previous_node.is_opening_bracket:
                open_brackets.append(previous_node)
            elif previous_node.is_opening_jinja_block:
                open_jinja_blocks.append(previous_node)

        # if the token should reduce the depth of the node, pop
        # the last item(s) off open_brackets or open_jinja_blocks
        if token.type == TokenType.UNTERM_KEYWORD:
            if open_brackets and open_brackets[-1].is_unterm_keyword:
                _ = open_brackets.pop()
        elif token.type in (TokenType.BRACKET_CLOSE, TokenType.STATEMENT_END):
            try:
                last_bracket = open_brackets.pop()
                if last_bracket.is_unterm_keyword:
                    last_bracket = open_brackets.pop()
            except IndexError:
                raise SqlfmtBracketError(
                    f"Closing bracket '{token.token}' found at "
                    f"{token.spos} before bracket was opened."
                )
            else:
                cls.raise_on_mismatched_bracket(token, last_bracket)
        elif token.type == TokenType.JINJA_BLOCK_END:
            try:
                _ = open_jinja_blocks.pop()
            except IndexError:
                raise SqlfmtBracketError(
                    f"Closing bracket '{token.token}' found at "
                    f"{token.spos} before bracket was opened."
                )
        # if we hit a semicolon, reset open_brackets, since we're
        # about to start a new query
        elif token.type == TokenType.SEMICOLON:
            open_brackets = []

        prev_token, extra_whitespace = cls.previous_token(previous_node)
        prefix = cls.whitespace(token, prev_token, extra_whitespace)
        value = cls.capitalize(token)

        if token.type in (TokenType.FMT_OFF, TokenType.DATA):
            formatting_disabled = True
        elif prev_token and prev_token.type in (TokenType.FMT_ON, TokenType.DATA):
            formatting_disabled = False

        return Node(
            token=token,
            previous_node=previous_node,
            prefix=prefix,
            value=value,
            open_brackets=open_brackets,
            open_jinja_blocks=open_jinja_blocks,
            formatting_disabled=formatting_disabled,
        )

    @classmethod
    def raise_on_mismatched_bracket(cls, token: Token, last_bracket: "Node") -> None:
        """
        Raise a SqlfmtBracketError if token is a closing bracket, but it
        does not match the token in the last_bracket node
        """
        matches = {
            "{": "}",
            "(": ")",
            "[": "]",
            "case": "end",
        }
        if (
            last_bracket.token.type
            not in (TokenType.BRACKET_OPEN, TokenType.STATEMENT_START)
            or last_bracket.value not in matches
            or matches[last_bracket.value] != token.token.lower()
        ):
            raise SqlfmtBracketError(
                f"Closing bracket '{token.token}' found at {token.spos} does not "
                f"match last opened bracket '{last_bracket.value}' found at "
                f"{last_bracket.token.spos}."
            )

    @classmethod
    def previous_token(
        cls, prev_node: Optional["Node"]
    ) -> Tuple[Optional[Token], bool]:
        """
        Returns the token of prev_node, unless prev_node is a
        newline or jinja statement, in which case it recurses
        """
        if not prev_node:
            return None, False
        t = prev_node.token
        if t.type in (
            TokenType.NEWLINE,
            TokenType.JINJA_STATEMENT,
            TokenType.JINJA_BLOCK_START,
            TokenType.JINJA_BLOCK_END,
            TokenType.JINJA_BLOCK_KEYWORD,
        ):
            prev, _ = cls.previous_token(prev_node.previous_node)
            return prev, True
        else:
            return t, False

    @classmethod
    def whitespace(
        cls,
        token: Token,
        previous_token: Optional[Token],
        extra_whitespace: bool,
    ) -> str:
        """
        Returns the proper whitespace before the token literal, to be set as the
        prefix of the Node.

        Most tokens should be prefixed by a simple space. Other cases are outlined
        below.
        """
        NO_SPACE = ""
        SPACE = " "

        # tokens that are never preceded by a space
        if token.type in (
            TokenType.BRACKET_CLOSE,
            TokenType.COLON,
            TokenType.DOUBLE_COLON,
            TokenType.COMMA,
            TokenType.DOT,
            TokenType.NEWLINE,
        ):
            return NO_SPACE
        # names preceded by dots or colons are namespaced identifiers. No space.
        elif (
            token.type
            in (
                TokenType.QUOTED_NAME,
                TokenType.NAME,
                TokenType.STAR,
                TokenType.JINJA_EXPRESSION,
            )
            and previous_token
            and previous_token.type in (TokenType.DOT, TokenType.COLON)
        ):
            return NO_SPACE
        # numbers preceded by colons are simple slices. No Space
        elif (
            token.type == TokenType.NUMBER
            and previous_token
            and previous_token.type == TokenType.COLON
        ):
            return NO_SPACE
        # open brackets that follow names are function calls or array indexes.
        # No Space.
        elif (
            token.type == TokenType.BRACKET_OPEN
            and previous_token
            and previous_token.type in (TokenType.NAME, TokenType.QUOTED_NAME)
        ):
            return NO_SPACE
        # need a space before any other open bracket
        elif token.type == TokenType.BRACKET_OPEN:
            return SPACE
        # no spaces after an open bracket or a cast operator (::)
        elif previous_token and previous_token.type in (
            TokenType.BRACKET_OPEN,
            TokenType.DOUBLE_COLON,
        ):
            return NO_SPACE
        # always a space before a keyword
        elif token.type in (
            TokenType.UNTERM_KEYWORD,
            TokenType.STATEMENT_START,
            TokenType.STATEMENT_END,
            TokenType.WORD_OPERATOR,
            TokenType.BOOLEAN_OPERATOR,
            TokenType.AS,
            TokenType.ON,
            TokenType.SEMICOLON,
        ):
            return SPACE
        # we don't know what a jinja expression will evaluate to,
        # so we have to respect the original text
        elif token.type in (
            TokenType.JINJA_STATEMENT,
            TokenType.JINJA_BLOCK_START,
            TokenType.JINJA_BLOCK_END,
            TokenType.JINJA_BLOCK_KEYWORD,
            TokenType.JINJA_EXPRESSION,
        ):
            if token.prefix != "" or extra_whitespace:
                return SPACE
            else:
                return NO_SPACE
        elif previous_token and previous_token.type == TokenType.JINJA_EXPRESSION:
            if token.prefix != "" or extra_whitespace:
                return SPACE
            else:
                return NO_SPACE
        else:
            return SPACE

    @classmethod
    def capitalize(cls, token: Token) -> str:
        """
        Proper style is to lowercase all keywords, statements, and names.
        If DB identifiers can't be lowercased, they should be quoted. This
        will likely need to be changed for Snowflake support.
        """
        if token.type in (
            TokenType.UNTERM_KEYWORD,
            TokenType.NAME,
            TokenType.STATEMENT_START,
            TokenType.STATEMENT_END,
            TokenType.WORD_OPERATOR,
            TokenType.AS,
            TokenType.ON,
            TokenType.BOOLEAN_OPERATOR,
        ):
            return token.token.lower()
        else:
            return token.token
