from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from sqlfmt.exception import SqlfmtError
from sqlfmt.token import Token, TokenType, split_after


class SqlfmtBracketError(SqlfmtError):
    pass


@dataclass
class Node:
    token: Token
    previous_node: Optional["Node"]
    inherited_depth: int
    prefix: str
    value: str
    depth: int
    change_in_depth: int
    open_brackets: List[Token] = field(default_factory=list)

    def __str__(self) -> str:
        return self.prefix + self.value

    def __repr__(self) -> str:
        """
        Because of self.previous_node, the default dataclass repr creates
        unusable output
        """
        prev = (
            f"Node(token={self.previous_node.token})" if self.previous_node else "None"
        )
        b = [str(t) for t in self.open_brackets]
        r = (
            f"Node(\n"
            f"\ttoken='{str(self.token)}',\n"
            f"\tprevious_node={prev},\n"
            f"\tinherited_depth={self.inherited_depth},\n"
            f"\tdepth={self.depth},\n"
            f"\tchange_in_depth={self.change_in_depth},\n"
            f"\tprefix='{self.prefix}',\n"
            f"\tvalue='{self.value}',\n"
            f"\topen_brackets={b}\n"
            f")"
        )
        return r

    def __len__(self) -> int:
        return len(str(self))

    @property
    def is_unterm_keyword(self) -> bool:
        return self.token.type == TokenType.UNTERM_KEYWORD

    @property
    def is_select(self) -> bool:
        """
        Return True if this could be the beginning of a select statement (this node is
        "select" or "with")
        """
        if self.token.type == TokenType.UNTERM_KEYWORD and self.value.lower() in (
            "with",
            "select",
        ):
            return True
        else:
            return False

    @property
    def is_comma(self) -> bool:
        return self.token.type == TokenType.COMMA

    @property
    def is_comment(self) -> bool:
        return self.token.type == TokenType.COMMENT

    @property
    def is_operator(self) -> bool:
        return self.token.type in (TokenType.OPERATOR, TokenType.WORD_OPERATOR)

    @property
    def is_newline(self) -> bool:
        return self.token.type == TokenType.NEWLINE

    @property
    def is_multiline(self) -> bool:
        if (
            self.token.type in (TokenType.COMMENT, TokenType.JINJA)
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
        if previous_node:
            inherited_depth = previous_node.depth + previous_node.change_in_depth
            open_brackets = previous_node.open_brackets.copy()
        else:
            inherited_depth = 0
            open_brackets = []

        depth, change_in_depth, open_brackets = cls.calculate_depth(
            token, inherited_depth, open_brackets
        )

        previous_token: Optional[Token] = None
        if previous_node is None or previous_node.token.type == TokenType.NEWLINE:
            is_first_on_line = True
        else:
            is_first_on_line = False
            previous_token = previous_node.token

        prefix = cls.whitespace(token, is_first_on_line, previous_token)
        value = cls.capitalize(token)

        return Node(
            token,
            previous_node,
            inherited_depth,
            prefix,
            value,
            depth,
            change_in_depth,
            open_brackets,
        )

    @classmethod
    def calculate_depth(
        cls, token: Token, inherited_depth: int, open_brackets: List[Token]
    ) -> Tuple[int, int, List[Token]]:
        """
        Calculates the depth statistics for a Node (depth, change_in_depth,
        open_brackets), based on the properties of its token. Depth determines
        indentation and line splitting in the formatted query.

        We're operating on a single token at a time; since the token can affect
        its own node's indentation and/or the indentation of the next node, we
        need to start with the "inherited" depth and then adjust the final
        depth of the node based on the contents of the token at the node.
        """
        change_before = 0
        change_after = 0

        if token.type == TokenType.UNTERM_KEYWORD:
            maybe_last_bracket: Optional[Token] = (
                open_brackets.pop() if open_brackets else None
            )
            if (
                maybe_last_bracket
                and maybe_last_bracket.type == TokenType.UNTERM_KEYWORD
            ):  # this is a kw like 'from' that follows another top keyword,
                # so we need to dedent
                change_before = -1
            elif (
                maybe_last_bracket
            ):  # it's an open paren that needs to go back on the stack
                open_brackets.append(maybe_last_bracket)

            open_brackets.append(token)
            change_after = 1

        elif token.type in (TokenType.BRACKET_OPEN, TokenType.STATEMENT_START):
            open_brackets.append(token)
            change_after = 1

        elif token.type in (TokenType.BRACKET_CLOSE, TokenType.STATEMENT_END):
            try:
                last_bracket: Token = open_brackets.pop()
                change_before = -1
                # if the closing bracket follows a keyword like "from",
                # we need to pop the next open bracket off the stack,
                # which should be the matching pair to the current token
                if last_bracket and last_bracket.type == TokenType.UNTERM_KEYWORD:
                    last_bracket = open_brackets.pop()
                    change_before -= 1
            except IndexError:
                raise SqlfmtBracketError(
                    f"Closing bracket '{token.token}' found at "
                    f"{token.spos} before bracket was opened."
                )
            matches = {
                "{": "}",
                "(": ")",
                "[": "]",
                "case": "end",
            }
            assert (
                last_bracket.type in (TokenType.BRACKET_OPEN, TokenType.STATEMENT_START)
                and matches[last_bracket.token.lower()] == token.token.lower()
            ), (
                f"Closing bracket '{token.token}' found at {token.spos} does not match "
                f"last opened bracket '{last_bracket.token}' found at "
                f"{last_bracket.spos}."
            )

        depth = inherited_depth + change_before

        return depth, change_after, open_brackets

    @classmethod
    def whitespace(
        cls,
        token: Token,
        is_first_on_line: bool,
        previous_token: Optional[Token],
    ) -> str:
        """
        Returns the proper whitespace before the token literal, to be set as the
        prefix of the Node.

        Most tokens should be prefixed by a simple space. Other cases are outlined
        below.
        """
        NO_SPACE = ""
        SPACE = " "

        if is_first_on_line:
            return NO_SPACE
        # tokens that are never preceded by a space
        elif token.type in (
            TokenType.BRACKET_CLOSE,
            TokenType.DOUBLE_COLON,
            TokenType.COMMA,
            TokenType.DOT,
            TokenType.NEWLINE,
        ):
            return NO_SPACE
        # names preceded by dots are namespaced identifiers. No space.
        elif (
            token.type in (TokenType.QUOTED_NAME, TokenType.NAME, TokenType.STAR)
            and previous_token
            and previous_token.type == TokenType.DOT
        ):
            return NO_SPACE
        # open brackets that follow names are function calls
        # (no space) unless the preceding name is "as"
        # (declaring a CTE) or "over" (declaring a window partition)
        elif (
            token.type == TokenType.BRACKET_OPEN
            and previous_token
            and previous_token.type == TokenType.NAME
            and previous_token.token.lower() not in ("over", "as", "in")
        ):
            return NO_SPACE
        elif token.type == TokenType.BRACKET_OPEN:
            return SPACE
        # no spaces after an open bracket or a cast operator (::)
        elif previous_token and previous_token.type in (
            TokenType.BRACKET_OPEN,
            TokenType.DOUBLE_COLON,
        ):
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
        ):
            return token.token.lower()
        else:
            return token.token


@dataclass
class Line:
    source_string: str
    previous_node: Optional[Node]  # last node of prior line, if any
    nodes: List[Node] = field(default_factory=list)
    depth: int = 0
    change_in_depth: int = 0
    open_brackets: List[Token] = field(default_factory=list)
    depth_split: Optional[int] = None
    first_comma: Optional[int] = None
    first_operator: Optional[int] = None

    def __str__(self) -> str:
        INDENT = " " * 4
        prefix = INDENT * self.depth
        return prefix + "".join([str(node) for node in self.nodes])

    def __len__(self) -> int:
        return len(str(self))

    def append_token(self, token: Token) -> None:
        """
        Creates a new Node from the passed token and the context of the current line,
        then appends that Node to self.nodes and updates line depth and split features
        as necessary
        """
        previous_node: Optional[Node]
        if self.nodes:
            previous_node = self.nodes[-1]
        else:
            previous_node = self.previous_node

        node = Node.from_token(token, previous_node)

        # update the line's depth stats from the node
        if not self.nodes:
            self.depth = node.depth
            self.change_in_depth = node.change_in_depth
            self.open_brackets = node.open_brackets
        else:
            self.change_in_depth = node.depth - self.depth + node.change_in_depth
            # if we have a keyword in the middle of a line, we need to split on that
            # keyword
            if (
                token.type == TokenType.UNTERM_KEYWORD
                and not self.starts_with_unterm_keyword
            ):
                self.depth_split = len(self.nodes)

        # otherwise, splits should happen outside in... if this line is increasing
        # depth, we should split on the first node that increases depth. If it is
        # decreasing depth, we should split on the last node that decreases depth
        change_over_node = node.depth - node.inherited_depth + node.change_in_depth
        split_index = len(self.nodes)
        if split_after(node.token.type):
            split_index += 1

        if token.type == TokenType.COMMENT:
            self.depth_split = split_index
        elif self.change_in_depth < 0 and change_over_node < 0 and split_index > 0:
            self.depth_split = split_index
        elif self.depth_split is None and node.change_in_depth > 0:
            self.depth_split = split_index

        if (
            token.type == TokenType.COMMA
            and node.open_brackets == self.open_brackets
            and self.first_comma is None
        ):
            self.first_comma = split_index
        elif (
            token.type in (TokenType.OPERATOR, TokenType.WORD_OPERATOR)
            and self.first_operator is None
        ):
            self.first_operator = split_index

        self.nodes.append(node)

    def maybe_append_newline(self) -> None:
        """
        Check to see if this Line already ends in a NEWLINE. If not,
        call append_newline
        """
        if self.nodes and self.nodes[-1].token.type == TokenType.NEWLINE:
            pass
        else:
            self.append_newline()

    def append_newline(self) -> None:
        """
        Create a new NEWLINE token and append it to the end of this line
        """
        previous_token: Optional[Token] = None
        if self.nodes:
            previous_token = self.nodes[-1].token
        elif self.previous_node:
            previous_token = self.previous_node.token

        if previous_token:
            spos = (previous_token.epos[0], previous_token.epos[1])
            epos = (previous_token.epos[0], previous_token.epos[1] + 1)
            source_line = previous_token.line
        else:
            spos = (0, 0)
            epos = (0, 1)
            source_line = ""

        nl = Token(
            type=TokenType.NEWLINE,
            prefix="",
            token="\n",
            spos=spos,
            epos=epos,
            line=source_line,
        )
        self.append_token(nl)

    @classmethod
    def from_nodes(
        cls,
        source_string: str,
        previous_node: Optional[Node],
        nodes: List[Node],
    ) -> "Line":
        """
        Creates and returns a new line from a list of Nodes. Useful for line
        splitting and merging
        """
        line = Line(
            source_string=source_string,
            previous_node=previous_node,
            depth=(
                previous_node.depth + previous_node.change_in_depth
                if previous_node
                else 0
            ),
        )
        for node in nodes:
            line.append_token(node.token)  # todo: optimize this.

        return line

    @property
    def tokens(self) -> List[Token]:
        tokens = []
        for node in self.nodes:
            tokens.append(node.token)
        return tokens

    @property
    def starts_with_select(self) -> bool:
        try:
            return self.nodes[0].is_select
        except IndexError:
            return False

    @property
    def starts_with_unterm_keyword(self) -> bool:
        try:
            return self.nodes[0].is_unterm_keyword
        except IndexError:
            return False

    @property
    def contains_unterm_keyword(self) -> bool:
        return any([n.is_unterm_keyword for n in self.nodes])

    @property
    def contains_comment(self) -> bool:
        return any([n.is_comment for n in self.nodes])

    @property
    def contains_operator(self) -> bool:
        return any([n.is_operator for n in self.nodes])

    @property
    def contains_multiline_node(self) -> bool:
        return any([n.is_multiline for n in self.nodes])

    @property
    def ends_with_comma(self) -> bool:
        try:
            if self.nodes[-1].is_comma:
                return True
            elif (
                len(self.nodes) > 1
                and self.nodes[-1].is_newline
                and self.nodes[-2].is_comma
            ):
                return True
            else:
                return False
        except IndexError:
            return False

    @property
    def ends_with_comment(self) -> bool:
        try:
            if self.nodes[-1].is_comment:
                return True
            elif (
                len(self.nodes) > 1
                and self.nodes[-1].is_newline
                and self.nodes[-2].is_comment
            ):
                return True
            else:
                return False
        except IndexError:
            return False

    @property
    def last_content_index(self) -> int:
        for i, node in enumerate(self.nodes):
            if node.is_comment or node.is_newline:
                return i - 1
        else:
            return i

    @property
    def is_standalone_comment(self) -> bool:
        if len(self.nodes) == 1 and self.ends_with_comment:
            return True
        elif (
            len(self.nodes) == 2
            and self.ends_with_comment
            and self.nodes[-1].is_newline
        ):
            return True
        else:
            return False

    @property
    def is_standalone_multiline_node(self) -> bool:
        if len(self.nodes) == 1 and self.contains_multiline_node:
            return True
        if (
            len(self.nodes) == 2
            and self.contains_multiline_node
            and self.nodes[-1].is_newline
        ):
            return True
        else:
            return False

    def is_too_long(self, max_length: int) -> bool:
        """
        Returns true if the rendered length of the line is strictly greater
        than max_length, and if the line isn't a standalone long comment or
        multiline node
        """
        if (
            len(self) > max_length
            and not self.contains_multiline_node
            and not self.is_standalone_comment
        ):
            return True
        else:
            return False

    @property
    def can_be_depth_split(self) -> bool:
        if (
            self.depth_split
            and self.depth_split < self.last_content_index + 1
            and not self.is_standalone_comment
            and not self.is_standalone_multiline_node
        ):
            return True
        else:
            return False

    @property
    def can_be_comment_split(self) -> bool:
        if (
            self.depth_split
            and self.ends_with_comment
            and not self.is_standalone_comment
            and not self.is_standalone_multiline_node
        ):
            return True
        else:
            return False

    @property
    def closes_bracket_from_previous_line(self) -> bool:
        if self.previous_node and self.previous_node.open_brackets and self.nodes:
            explicit_brackets = [
                b
                for b in self.previous_node.open_brackets
                if b.type in (TokenType.STATEMENT_START, TokenType.BRACKET_OPEN)
            ]
            if (
                explicit_brackets
                and explicit_brackets[-1] not in self.nodes[-1].open_brackets
            ):
                return True
        return False
