from dataclasses import dataclass, field
from functools import cached_property
from io import StringIO
from typing import List, Optional, Tuple

from sqlfmt.dialect import Dialect
from sqlfmt.token import Token, TokenType


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

    @classmethod
    def from_token(cls, token: Token, previous_node: Optional["Node"]) -> "Node":
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

        prefix = cls.whitespace(token, is_first_on_line, depth, previous_token)
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
        # we're operating on a single token at a time; since the token can affect
        # its own node's indentation and/or the indentation of the next node, we
        # need to start with the "inherited" depth and then adjust the final
        # indention of the node based on the contents of the token at the node
        change_before = 0
        change_after = 0

        if token.type == TokenType.TOP_KEYWORD:
            maybe_last_bracket: Optional[Token] = (
                open_brackets.pop() if open_brackets else None
            )
            if (
                maybe_last_bracket and maybe_last_bracket.type == TokenType.TOP_KEYWORD
            ):  # this is a kw like 'from' that follows another top keyword,
                # so we need to dedent
                change_before = -1
            elif (
                maybe_last_bracket
            ):  # it's an open paren that needs to go back on the stack
                open_brackets.append(maybe_last_bracket)

            open_brackets.append(token)
            change_after = 1

        elif token.type == TokenType.BRACKET_OPEN:
            open_brackets.append(token)
            change_after = 1

        elif token.type == TokenType.BRACKET_CLOSE:
            try:
                last_bracket: Token = open_brackets.pop()
                if last_bracket and last_bracket.type == TokenType.TOP_KEYWORD:
                    last_bracket = open_brackets.pop()
            except IndexError:
                raise ValueError(
                    f"Closing bracket '{token.token}' found at "
                    f"{token.spos} before bracket was opened."
                )
            matches = {
                "{": "}",
                "(": ")",
                "[": "]",
            }
            assert (
                last_bracket.type == TokenType.BRACKET_OPEN
                and matches[last_bracket.token] == token.token
            ), (
                f"Closing bracket '{token.token}' found at {token.spos} does not match "
                f"last opened bracket '{last_bracket.token}' found at "
                f"{last_bracket.spos}."
            )
            change_before = -1

        elif token.type == TokenType.STATEMENT_START:
            change_after = 1
        elif token.type == TokenType.STATEMENT_END:
            change_before = -1

        depth = inherited_depth + change_before

        return depth, change_after, open_brackets

    @classmethod
    def whitespace(
        cls,
        token: Token,
        is_first_on_line: bool,
        depth: int,
        previous_token: Optional[Token],
    ) -> str:
        if is_first_on_line:
            INDENT = " " * 4
            return INDENT * depth
        elif token.type in (
            TokenType.BRACKET_CLOSE,
            TokenType.DOUBLE_COLON,
            TokenType.COMMA,
            TokenType.DOT,
            TokenType.NEWLINE,
        ):
            return ""
        elif (
            token.type in (TokenType.QUOTED_NAME, TokenType.NAME)
            and previous_token
            and previous_token.type == TokenType.DOT
        ):
            return ""
        elif previous_token and previous_token.type in (
            TokenType.BRACKET_OPEN,
            TokenType.DOUBLE_COLON,
        ):
            return ""
        else:
            return " "

    @classmethod
    def capitalize(cls, token: Token) -> str:
        if token.type in (
            TokenType.TOP_KEYWORD,
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
    lnum: int
    previous_node: Optional[Node]  # last node of prior line, if any
    nodes: List[Node] = field(default_factory=list)
    depth: int = 0

    def append_token(self, token: Token) -> None:
        """
        Creates a new Node from the passed token and the context of the current line,
        then appends that Node to self.nodes and updates line depth as necessary
        """
        previous_node: Optional[Node]
        if self.nodes:
            previous_node = self.nodes[-1]
        else:
            previous_node = self.previous_node

        node = Node.from_token(token, previous_node)

        # if the first node on a line, update the line's depth from the node
        if not self.nodes:
            self.depth = node.depth

        self.nodes.append(node)

    @property
    def tokens(self) -> List[Token]:
        tokens = []
        for node in self.nodes:
            tokens.append(node.token)
        return tokens

    def __str__(self) -> str:
        if self.nodes:
            parts = []
            for node in self.nodes:
                parts.append(str(node))
            return "".join(parts)
        else:
            return ""

    def __len__(self) -> int:
        return len(str(self))


@dataclass
class Query:
    source_string: str
    dialect: Dialect
    lines: List[Line] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.tokenize_from_source()
        self.split_and_merge_lines()

    def tokenize_from_source(self) -> None:
        """Updates self.lines and self.tokens from source_string"""
        if not self.source_string:
            return

        if self.lines and self.tokens:
            # don't run this again
            return

        buffer = StringIO(self.source_string)

        for lnum, line in enumerate(buffer.readlines()):
            current_line = Line(
                source_string=line,
                lnum=lnum,
                previous_node=self.lines[-1].nodes[-1] if self.lines else None,
            )
            for token in self.dialect.tokenize_line(line=line, lnum=lnum):
                # nodes are formatted as tokens are appended,
                # but splitting lines happens later
                current_line.append_token(token)

            self.lines.append(current_line)

    def split_and_merge_lines(self) -> None:
        """Mutates self.lines to enforce line length and other splitting
        rules"""
        pass

    @property
    def tokens(self) -> List[Token]:
        tokens: List[Token] = []
        for line in self.lines:
            tokens.extend(line.tokens)
        return tokens

    @property
    def nodes(self) -> List[Node]:
        nodes: List[Node] = []
        for line in self.lines:
            nodes.extend(line.nodes)
        return nodes

    @cached_property
    def formatted_string(self) -> str:
        draft = []
        for s in [str(line) for line in self.lines]:
            if s:
                draft.append(s)

        q = "".join(draft)
        return q
