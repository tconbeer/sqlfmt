from typing import Optional

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

        prev_token, extra_whitespace = get_previous_token(previous_node)
        prefix = self.whitespace(token, prev_token, extra_whitespace)
        value = self.standardize_value(token)

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
        # open brackets that follow closing brackets are array indexes.
        # open brackets that follow open brackets are just nested brackets.
        # No Space.
        elif (
            token.type == TokenType.BRACKET_OPEN
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

    def standardize_value(self, token: Token) -> str:
        """
        Tokens that are words (not symbols) and aren't jinja
        or comments should be lowercased and have any internal
        whitespace replaced with a single space
        """
        if token.type in (
            TokenType.UNTERM_KEYWORD,
            TokenType.STATEMENT_START,
            TokenType.STATEMENT_END,
            TokenType.WORD_OPERATOR,
            TokenType.ON,
            TokenType.BOOLEAN_OPERATOR,
            TokenType.SET_OPERATOR,
        ):
            return " ".join(token.token.lower().split())
        elif token.type == TokenType.NAME and not self.case_sensitive_names:
            return token.token.lower()
        else:
            return token.token

    def append_newline(self, line: Line) -> None:
        """
        Create a new NEWLINE token and append it to the end of line
        """
        previous_node: Optional[Node] = None
        previous_token: Optional[Token] = None
        if line.nodes:
            previous_node = line.nodes[-1]
            previous_token = line.nodes[-1].token
        elif line.previous_node:
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
