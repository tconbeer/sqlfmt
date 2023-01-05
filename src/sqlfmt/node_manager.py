import re
from typing import List, Optional, Tuple

from sqlfmt.exception import SqlfmtBracketError
from sqlfmt.line import Line
from sqlfmt.node import Node, get_previous_token
from sqlfmt.token import Token, TokenType


class NodeManager:
    def __init__(self, case_sensitive_names: bool) -> None:
        self.case_sensitive_names = case_sensitive_names

    def create_node(self, token: Token, previous_node: Optional[Node]) -> Node:
        """
        Create a Node from a Token. For the Node to be properly formatted,
        method call must also include a reference to the previous Node in the
        Query (either on the same or previous Line), unless it is the first
        Node in the Query.

        The Node's depth and whitespace are calculated when it is created
        (this does most of the formatting of the Node). Node values are
        lowercased if they are simple names, keywords, or statements.
        """

        open_brackets, open_jinja_blocks = self.open_brackets(token, previous_node)
        formatting_disabled = self.disable_formatting(token, previous_node)
        if formatting_disabled:
            prefix = token.prefix
            value = token.token
        else:
            prev_token, extra_whitespace = get_previous_token(previous_node)
            prefix = self.whitespace(token, prev_token, extra_whitespace)
            value = self.standardize_value(token)

        return Node(
            token=token,
            previous_node=previous_node,
            prefix=prefix,
            value=value,
            open_brackets=open_brackets,
            open_jinja_blocks=open_jinja_blocks,
            formatting_disabled=formatting_disabled,
        )

    def raise_on_mismatched_bracket(self, token: Token, last_bracket: Node) -> None:
        """
        Raise a SqlfmtBracketError if token is a closing bracket, but it
        does not match the token in the last_bracket node
        """
        matches = {
            "{": "}",
            "(": ")",
            "[": "]",
            "case": "end",
            "array<": ">",
            "table<": ">",
            "struct<": ">",
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

    def raise_on_mismatched_jinja_tags(self, token: Token, start_tag: Node) -> None:
        """
        Compare the value of token to the start_tag to determine whether token
        closes start_tag
        """
        try:
            if any(s in token.token.lower() for s in ["endif", "else", "elif"]):
                if not any(s in start_tag.value for s in ["if", "else"]):
                    raise ValueError
            else:
                end_text, _ = re.subn(r"[{}%\-\s]", "", token.token.lower())
                start_value = end_text.replace("end", "")
                if start_value not in start_tag.value:
                    raise ValueError
        except ValueError:
            raise SqlfmtBracketError(
                f"Closing jinja tag '{token.token}' found at pos {token.spos} does "
                f"not match last opened tag '{start_tag.value}' found at pos "
                f"{start_tag.token.spos}."
            )

    def open_brackets(
        self, token: Token, previous_node: Optional[Node]
    ) -> Tuple[List[Node], List[Node]]:
        """
        Uses the previous_node and the contents of the current token
        to compute the depth of the new node.

        Returns two lists, for open_brackets and open_jinja_blocks
        """

        if previous_node is None:
            open_brackets = []
            open_jinja_blocks = []
        else:
            open_brackets = previous_node.open_brackets.copy()
            open_jinja_blocks = previous_node.open_jinja_blocks.copy()

            # add the previous node to the list of open brackets or jinja blocks
            if previous_node.is_unterm_keyword or previous_node.is_opening_bracket:
                open_brackets.append(previous_node)
            elif previous_node.is_opening_jinja_block:
                open_jinja_blocks.append(previous_node)

        # if the token should reduce the depth of the node, pop
        # the last item(s) off open_brackets or open_jinja_blocks
        if token.type in (TokenType.UNTERM_KEYWORD, TokenType.SET_OPERATOR):
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
                self.raise_on_mismatched_bracket(token, last_bracket)
        elif token.type is TokenType.JINJA_BLOCK_END:
            try:
                start_tag = open_jinja_blocks.pop()
                self.raise_on_mismatched_jinja_tags(token, start_tag)
            except IndexError:
                raise SqlfmtBracketError(
                    f"Closing bracket '{token.token}' found at "
                    f"{token.spos} before bracket was opened."
                )
        # if we hit a semicolon, reset open_brackets, since we're
        # about to start a new query
        elif token.type is TokenType.SEMICOLON:
            open_brackets = []

        return open_brackets, open_jinja_blocks

    def whitespace(
        self,
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
        if token.type.is_never_preceded_by_space:
            return NO_SPACE
        # no spaces after an open bracket or a cast operator (::)
        elif previous_token and previous_token.type in (
            TokenType.BRACKET_OPEN,
            TokenType.DOUBLE_COLON,
        ):
            return NO_SPACE
        # always a space before a keyword
        elif token.type.is_preceded_by_space_except_after_open_bracket:
            return SPACE
        # names preceded by dots or colons are namespaced identifiers. No space.
        elif (
            token.type.is_possible_name
            and previous_token
            and previous_token.type in (TokenType.DOT, TokenType.COLON)
        ):
            return NO_SPACE
        # numbers preceded by colons are simple slices. No Space
        elif (
            token.type is TokenType.NUMBER
            and previous_token
            and previous_token.type is TokenType.COLON
        ):
            return NO_SPACE
        # open brackets that contain `<` are bq type definitions
        # like `array<` in `array<int64>` and require a space,
        # unless the preceding token is also an open bracket
        elif token.type is TokenType.BRACKET_OPEN and "<" in token.token:
            if previous_token and previous_token.type is not TokenType.BRACKET_OPEN:
                return SPACE
            else:
                return NO_SPACE
        # open brackets that follow names are function calls or array indexes.
        # open brackets that follow closing brackets are array indexes.
        # open brackets that follow open brackets are just nested brackets.
        # No Space.
        elif (
            token.type is TokenType.BRACKET_OPEN
            and previous_token
            and previous_token.type
            in (
                TokenType.NAME,
                TokenType.QUOTED_NAME,
                TokenType.BRACKET_OPEN,
                TokenType.BRACKET_CLOSE,
            )
        ):
            return NO_SPACE
        # need a space before any other open bracket
        elif token.type is TokenType.BRACKET_OPEN:
            return SPACE
        # we don't know what a jinja expression will evaluate to,
        # so we have to respect the original text
        elif token.type.is_jinja:
            if token.prefix != "" or extra_whitespace:
                return SPACE
            else:
                return NO_SPACE
        elif previous_token and previous_token.type is TokenType.JINJA_EXPRESSION:
            if token.prefix != "" or extra_whitespace:
                return SPACE
            else:
                return NO_SPACE
        else:
            return SPACE

    def standardize_value(self, token: Token) -> str:
        """
        Tokens that are words (not symbols) and aren't jinja
        or comments should be lowercased and have any internal
        whitespace replaced with a single space
        """
        if token.type.is_always_lowercased:
            return " ".join(token.token.lower().split())
        elif token.type is TokenType.NAME and not self.case_sensitive_names:
            return token.token.lower()
        else:
            return token.token

    def disable_formatting(
        self, token: Token, previous_node: Optional[Node]
    ) -> List[Token]:
        """
        Manage the formatting_disabled property for the node to be created from
        the token and previous node.
        """
        formatting_disabled = (
            previous_node.formatting_disabled.copy()
            if previous_node is not None
            else []
        )

        if token.type in (TokenType.FMT_OFF, TokenType.DATA):
            formatting_disabled.append(token)

        if (
            formatting_disabled
            and previous_node is not None
            and previous_node.token.type
            in (
                TokenType.FMT_ON,
                TokenType.DATA,
            )
        ):
            formatting_disabled.pop()

        # formatting can be disabled because of unsupported
        # ddl. When we hit a semicolon we need to pop
        # all of the formatting disabled tokens caused by ddl
        # off the stack
        if token.type is TokenType.SEMICOLON:
            while (
                formatting_disabled
                and "fmt:" not in formatting_disabled[-1].token.lower()
            ):
                formatting_disabled.pop()

        return formatting_disabled

    def append_newline(self, line: Line) -> None:
        """
        Create a new NEWLINE token and append it to the end of line
        """
        previous_node: Optional[Node] = None
        previous_token: Optional[Token] = None
        if line.nodes:
            previous_node = line.nodes[-1]
            previous_token = line.nodes[-1].token
        elif line.previous_node is not None:
            previous_node = line.previous_node
            previous_token = line.previous_node.token

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

        node = self.create_node(token=nl, previous_node=previous_node)
        line.nodes.append(node)
