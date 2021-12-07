from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from sqlfmt.exception import SqlfmtError
from sqlfmt.token import Token, TokenType, split_after


class SqlfmtBracketError(SqlfmtError):
    pass


@dataclass
class Comment:
    token: Token
    is_standalone: bool

    def __str__(self) -> str:
        return self.token.token + "\n"

    def __len__(self) -> int:
        return len(str(self))


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
    formatting_disabled: bool = False

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
            f"\tformatting_disabled={self.formatting_disabled}\n"
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
            formatting_disabled = previous_node.formatting_disabled
        else:
            inherited_depth = 0
            open_brackets = []
            formatting_disabled = False

        depth, change_in_depth, open_brackets = cls.calculate_depth(
            token, inherited_depth, open_brackets
        )

        def previous_token(prev_node: Optional[Node]) -> Optional[Token]:
            """
            Returns the token of prev_node, unless prev_node is a
            newline, in which case it recurses
            """
            if not prev_node:
                return None
            t = prev_node.token
            if t.type == TokenType.NEWLINE:
                return previous_token(prev_node.previous_node)
            else:
                return t

        prev_token = previous_token(previous_node)

        prefix = cls.whitespace(token, prev_token)
        value = cls.capitalize(token)

        if token.type == TokenType.FMT_OFF:
            formatting_disabled = True
        elif prev_token and prev_token.type == TokenType.FMT_ON:
            formatting_disabled = False

        return Node(
            token,
            previous_node,
            inherited_depth,
            prefix,
            value,
            depth,
            change_in_depth,
            open_brackets,
            formatting_disabled,
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
            try:
                assert (
                    last_bracket.type
                    in (TokenType.BRACKET_OPEN, TokenType.STATEMENT_START)
                    and matches[last_bracket.token.lower()] == token.token.lower()
                )
            except AssertionError:
                raise SqlfmtBracketError(
                    f"Closing bracket '{token.token}' found at {token.spos} does not "
                    f"match last opened bracket '{last_bracket.token}' found at "
                    f"{last_bracket.spos}."
                )

        depth = inherited_depth + change_before

        return depth, change_after, open_brackets

    @classmethod
    def whitespace(
        cls,
        token: Token,
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

        # tokens that are never preceded by a space
        if token.type in (
            TokenType.BRACKET_CLOSE,
            TokenType.DOUBLE_COLON,
            TokenType.COMMA,
            TokenType.DOT,
            TokenType.NEWLINE,
        ):
            return NO_SPACE
        # names preceded by dots are namespaced identifiers. No space.
        elif (
            token.type
            in (TokenType.QUOTED_NAME, TokenType.NAME, TokenType.STAR, TokenType.JINJA)
            and previous_token
            and previous_token.type == TokenType.DOT
        ):
            return NO_SPACE
        # open brackets that follow names are function calls. No Space.
        elif (
            token.type == TokenType.BRACKET_OPEN
            and previous_token
            and previous_token.type == TokenType.NAME
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
            TokenType.WORD_OPERATOR,
        ):
            return token.token.lower()
        else:
            return token.token


@dataclass
class Line:
    source_string: str
    previous_node: Optional[Node]  # last node of prior line, if any
    nodes: List[Node] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)
    depth: int = 0
    change_in_depth: int = 0
    open_brackets: List[Token] = field(default_factory=list)
    formatting_disabled: bool = False

    def __str__(self) -> str:
        if self.formatting_disabled:
            return "".join([f"{t.prefix}{t.token}" for t in self.tokens])
        else:
            return self.prefix + "".join([str(node) for node in self.nodes]).lstrip(" ")

    def __len__(self) -> int:
        return len(str(self))

    @property
    def prefix(self) -> str:
        INDENT = " " * 4
        prefix = INDENT * self.depth
        return prefix

    def render_with_comments(self, max_length: int) -> str:
        content = str(self)
        if len(self.comments) == 0:
            return content
        elif len(self.comments) == 1:
            # standalone or multiline comment
            if self.nodes[0].is_newline:
                return self.prefix + str(self.comments[0])
            # inline comment
            elif (not self.comments[0].is_standalone) and (
                len(content) + 1 + len(self.comments[0]) <= max_length
            ):
                return content.rstrip() + " " + str(self.comments[0])
            # wrap comment above
            else:
                return self.prefix + str(self.comments[0]) + content
        # wrap comments above; note that str(comment) is newline-terminated
        else:
            comment_str = "".join([self.prefix + str(c) for c in self.comments])
            return comment_str + content

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

        split_index = len(self.nodes)
        if split_after(node.token.type):
            split_index += 1

        self.formatting_disabled = self.formatting_disabled or node.formatting_disabled

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
            spos = previous_token.epos
            epos = spos
        else:
            spos = 0
            epos = 0

        nl = Token(
            type=TokenType.NEWLINE,
            prefix="",
            token="\n",
            spos=spos,
            epos=epos,
        )
        self.append_token(nl)

    @classmethod
    def from_nodes(
        cls,
        source_string: str,
        previous_node: Optional[Node],
        nodes: List[Node],
        comments: List[Comment],
    ) -> "Line":
        """
        Creates and returns a new line from a list of Nodes. Useful for line
        splitting and merging
        """
        nodes[0].previous_node = previous_node
        line = Line(
            source_string=source_string,
            previous_node=previous_node,
            nodes=nodes,
            comments=comments,
            depth=nodes[0].depth,
            change_in_depth=(
                nodes[-1].depth - nodes[0].depth + nodes[-1].change_in_depth
            ),
            open_brackets=nodes[0].open_brackets,
            formatting_disabled=nodes[0].formatting_disabled
            or nodes[-1].formatting_disabled,
        )

        return line

    @property
    def tokens(self) -> List[Token]:
        tokens = []
        for node in self.nodes:
            tokens.append(node.token)
        return tokens

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
    def contains_operator(self) -> bool:
        return any([n.is_operator for n in self.nodes])

    @property
    def contains_multiline_node(self) -> bool:
        return any([n.is_multiline for n in self.nodes])

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
        than max_length, and if the line isn't a standalone long
        multiline node
        """
        if len(self) > max_length and not self.contains_multiline_node:
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
