import re
import sys
from dataclasses import dataclass, field
from typing import Iterator, List, Optional, Tuple

from sqlfmt.exception import InlineCommentError, SqlfmtBracketError
from sqlfmt.token import Token, TokenType

if sys.version_info >= (3, 8):
    from functools import cached_property
else:
    from backports.cached_property import cached_property

COMMENT_PROGRAM = re.compile(r"(--|#|/\*|\{#-?)([^\S\n]*)")


@dataclass
class Comment:
    token: Token
    is_standalone: bool

    def __str__(self) -> str:
        return self._calc_str

    @cached_property
    def _calc_str(self) -> str:
        if self.is_multiline:
            return self.token.token + "\n"
        else:
            marker, comment_text = self._comment_parts()
            return marker + " " + comment_text + "\n"

    def __len__(self) -> int:
        return len(str(self))

    def _get_marker(self) -> Tuple[str, int]:
        match = COMMENT_PROGRAM.match(self.token.token)
        assert match, f"{self.token.token} does not match comment marker"
        _, epos = match.span(1)
        _, len = match.span(2)
        return self.token.token[:epos], len

    def _comment_parts(self) -> Tuple[str, str]:
        assert not self.is_multiline
        marker, skipchars = self._get_marker()
        comment_text = self.token.token[skipchars:]
        return marker, comment_text

    @property
    def is_multiline(self) -> bool:
        return "\n" in self.token.token

    def render_inline(self, max_length: int, content_length: int) -> str:
        if self.is_standalone:
            raise InlineCommentError("Can't inline standalone comment")
        else:
            inline_prefix = " " * 2
            rendered = inline_prefix + str(self)
            if content_length + len(rendered) > max_length:
                raise InlineCommentError("Comment too long to be inlined")
            else:
                return inline_prefix + str(self)

    def render_standalone(self, max_length: int, prefix: str) -> str:
        if self.is_multiline:
            # todo: split lines, indent each line the same
            return prefix + str(self)
        else:
            if len(self) + len(prefix) <= max_length:
                return prefix + str(self)
            else:
                marker, comment_text = self._comment_parts()
                if marker in ("--", "#"):
                    available_length = max_length - len(prefix) - len(marker) - 2
                    line_gen = self._split_before(comment_text, available_length)
                    return "".join(
                        [prefix + marker + " " + txt + "\n" for txt in line_gen]
                    )
                else:  # block-style or jinja comment. Don't wrap long lines for now
                    return prefix + str(self)

    @classmethod
    def _split_before(cls, text: str, max_length: int) -> Iterator[str]:
        if len(text) < max_length:
            yield text.rstrip()
        else:
            for idx, char in enumerate(reversed(text[:max_length])):
                if char.isspace():
                    yield text[: max_length - idx].rstrip()
                    yield from cls._split_before(text[max_length - idx :], max_length)
                    break
            else:  # no spaces in the comment
                yield text.rstrip()


@dataclass
class Node:
    token: Token
    previous_node: Optional["Node"]
    prefix: str
    value: str
    open_brackets: List["Node"] = field(default_factory=list)
    open_jinja_blocks: List["Node"] = field(default_factory=list)
    formatting_disabled: bool = False

    def __str__(self) -> str:
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
        return len(str(self))

    @property
    def depth(self) -> Tuple[int, int]:
        return (len(self.open_brackets), len(self.open_jinja_blocks))

    @property
    def is_unterm_keyword(self) -> bool:
        return self.token.type == TokenType.UNTERM_KEYWORD

    @property
    def is_comma(self) -> bool:
        return self.token.type == TokenType.COMMA

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
    def is_multiplication_star(self) -> bool:
        if self.token.type != TokenType.STAR:
            return False
        prev_token = self.previous_token(self.previous_node)
        if not prev_token:
            return False
        else:
            return not (
                prev_token.type
                in (TokenType.UNTERM_KEYWORD, TokenType.COMMA, TokenType.DOT)
            )

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
            elif previous_node.token.type in (
                TokenType.JINJA_BLOCK_START,
                TokenType.JINJA_BLOCK_KEYWORD,
            ):
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

        prev_token = cls.previous_token(previous_node)
        prefix = cls.whitespace(token, prev_token)
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
    def previous_token(cls, prev_node: Optional["Node"]) -> Optional[Token]:
        """
        Returns the token of prev_node, unless prev_node is a
        newline or jinja statement, in which case it recurses
        """
        if not prev_node:
            return None
        t = prev_node.token
        if t.type in (
            TokenType.NEWLINE,
            TokenType.JINJA_STATEMENT,
            TokenType.JINJA_BLOCK_START,
            TokenType.JINJA_BLOCK_END,
            TokenType.JINJA_BLOCK_KEYWORD,
        ):
            return cls.previous_token(prev_node.previous_node)
        else:
            return t

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
            TokenType.JINJA_STATEMENT,
            TokenType.JINJA_BLOCK_START,
            TokenType.JINJA_BLOCK_END,
            TokenType.JINJA_BLOCK_KEYWORD,
        ):
            return NO_SPACE
        # names preceded by dots are namespaced identifiers. No space.
        elif (
            token.type
            in (
                TokenType.QUOTED_NAME,
                TokenType.NAME,
                TokenType.STAR,
                TokenType.JINJA_EXPRESSION,
            )
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
        # we don't know what a jinja expression will evaluate to,
        # so we have to respect the original text
        elif token.type == TokenType.JINJA_EXPRESSION:
            if token.prefix == "":
                return NO_SPACE
            else:
                return SPACE
        elif previous_token and previous_token.type == TokenType.JINJA_EXPRESSION:
            if token.prefix == "":
                return NO_SPACE
            else:
                return SPACE
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


@dataclass
class Line:
    previous_node: Optional[Node]  # last node of prior line, if any
    nodes: List[Node] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)
    formatting_disabled: bool = False

    def __str__(self) -> str:
        return self._calc_str

    @cached_property
    def _calc_str(self) -> str:
        if self.formatting_disabled:
            return "".join([f"{t.prefix}{t.token}" for t in self.tokens])
        else:
            return self.prefix + "".join([str(node) for node in self.nodes]).lstrip(" ")

    def __len__(self) -> int:
        try:
            return max([len(s) for s in str(self).splitlines()])
        except ValueError:
            return 0

    @property
    def open_brackets(self) -> List[Node]:
        if self.nodes:
            return self.nodes[0].open_brackets
        elif self.previous_node:
            return self.previous_node.open_brackets
        else:
            return []

    @property
    def open_jinja_blocks(self) -> List[Node]:
        if self.nodes:
            return self.nodes[0].open_jinja_blocks
        elif self.previous_node:
            return self.previous_node.open_jinja_blocks
        else:
            return []

    @property
    def depth(self) -> Tuple[int, int]:
        if self.nodes:
            return (len(self.open_brackets), len(self.open_jinja_blocks))
        else:
            return (0, 0)

    @property
    def prefix(self) -> str:
        INDENT = " " * 4
        prefix = INDENT * self.depth[0]
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
            else:
                try:
                    comment = self.comments[0].render_inline(
                        max_length=max_length, content_length=len(content.rstrip())
                    )
                    return content.rstrip() + comment
                except InlineCommentError:
                    comment = self.comments[0].render_standalone(
                        max_length=max_length, prefix=self.prefix
                    )
                    return comment + content
        # wrap comments above; note that str(comment) is newline-terminated
        else:
            comment_str = "".join(
                [
                    c.render_standalone(max_length=max_length, prefix=self.prefix)
                    for c in self.comments
                ]
            )
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

        self.formatting_disabled = self.formatting_disabled or node.formatting_disabled

        self.nodes.append(node)

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
        previous_node: Optional[Node],
        nodes: List[Node],
        comments: List[Comment],
    ) -> "Line":
        """
        Creates and returns a new line from a list of Nodes. Useful for line
        splitting and merging
        """
        if nodes:
            nodes[0].previous_node = previous_node
            line = Line(
                previous_node=previous_node,
                nodes=nodes,
                comments=comments,
                formatting_disabled=nodes[0].formatting_disabled
                or nodes[-1].formatting_disabled,
            )
        else:
            line = Line(
                previous_node=previous_node,
                nodes=nodes,
                comments=comments,
                formatting_disabled=previous_node.formatting_disabled
                if previous_node
                else False,
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
    def starts_with_operator(self) -> bool:
        try:
            return self.nodes[0].is_operator
        except IndexError:
            return False

    @property
    def starts_with_low_priority_merge_operator(self) -> bool:
        try:
            return self.nodes[0].is_low_priority_merge_operator
        except IndexError:
            return False

    @property
    def starts_with_comma(self) -> bool:
        try:
            return self.nodes[0].is_comma
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

    @property
    def is_standalone_jinja_statement(self) -> bool:
        if len(self.nodes) == 1 and self.nodes[0].is_jinja_statement:
            return True
        if (
            len(self.nodes) == 2
            and self.nodes[0].is_jinja_statement
            and self.nodes[1].is_newline
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
        if len(self) > max_length:
            return True
        else:
            return False

    @property
    def closes_bracket_from_previous_line(self) -> bool:
        """
        Returns true for a line with an explicit bracket like ")" or "]"
        that matches a bracket on a preceding line. False for unterminated
        keywords or any lines with matched brackets
        """
        if self.previous_node and self.previous_node.open_brackets and self.nodes:
            explicit_brackets = [
                b for b in self.previous_node.open_brackets if b.is_opening_bracket
            ]
            if (
                explicit_brackets
                and explicit_brackets[-1] not in self.nodes[-1].open_brackets
            ):
                return True
        return False

    @property
    def closes_jinja_block_from_previous_line(self) -> bool:
        """
        Returns true for a line that contains {% endif %}, {% endfor %}, etc.
        where the matching {% if %}, etc. is on a previous line. Returns False
        for {% else %}/{% elif %} or an {% endif %} that follows an {% else %}/
        {% endif %}
        """
        if (
            self.previous_node
            and self.previous_node.open_jinja_blocks
            and not self.previous_node.open_jinja_blocks[-1].is_jinja_block_keyword
            and self.nodes
            and (
                self.previous_node.open_jinja_blocks[-1]
                not in self.nodes[-1].open_jinja_blocks
            )
            and (
                not self.nodes[-1].open_jinja_blocks
                or not self.nodes[-1].open_jinja_blocks[-1].is_jinja_block_keyword
            )
        ):
            return True
        return False

    @property
    def opens_new_bracket(self) -> bool:
        if not self.nodes:
            return False
        elif not self.nodes[-1].open_brackets:
            return False
        else:
            b = self.nodes[-1].open_brackets[-1]
            if b.is_opening_bracket and b not in self.open_brackets:
                return True
            else:
                return False
