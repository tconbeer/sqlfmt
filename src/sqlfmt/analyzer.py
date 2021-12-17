import re
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional

from sqlfmt.exception import SqlfmtError
from sqlfmt.line import Comment, Line, Node
from sqlfmt.query import Query
from sqlfmt.token import Token, TokenType

MAYBE_WHITESPACES: str = r"[^\S\n]*"  # any whitespace except newline


def group(*choices: str) -> str:
    return "(" + "|".join(choices) + ")"


class SqlfmtMultilineError(SqlfmtError):
    pass


class SqlfmtParsingError(SqlfmtError):
    pass


class Rule:
    name: str
    priority: int  # lower get matched first
    pattern: str
    action: Callable

    def __post_init__(self) -> None:
        self.program = re.compile(
            MAYBE_WHITESPACES + self.pattern, re.IGNORECASE | re.DOTALL
        )


@dataclass
class Analyzer:
    # rules: List[Rule]
    line_length: int
    patterns: Dict[TokenType, str]
    programs: Dict[TokenType, re.Pattern]
    node_buffer: List[Node] = field(default_factory=list)
    comment_buffer: List[Comment] = field(default_factory=list)
    line_buffer: List[Line] = field(default_factory=list)
    previous_node: Optional[Node] = None
    previous_line_node: Optional[Node] = None

    def flush_buffers(self) -> None:
        self.node_buffer = []
        self.comment_buffer = []

    def parse_query(self, source_string: str) -> Query:
        """
        Initialize a parser and parse the source string, return
        a structured Query.
        """
        q = Query(source_string, line_length=self.line_length)

        for token in self.lex_old(source_string=source_string, pos=0):
            if token.type in (TokenType.COMMENT, TokenType.JINJA_COMMENT):
                self._handle_comment(token)
            elif token.type == TokenType.NEWLINE:
                self._handle_newline(token)
            else:
                self._handle_token(token)
        # append a final line if the file doesn't end with a newline
        if self.node_buffer:
            line = Line.from_nodes(
                source_string="",
                previous_node=self.previous_line_node,
                nodes=self.node_buffer,
                comments=self.comment_buffer,
            )
            line.append_newline()
            self.line_buffer.append(line)
        q.lines = self.line_buffer
        return q

    def _handle_comment(self, token: Token) -> None:
        is_standalone = (not bool(self.node_buffer)) or "\n" in token.token
        comment = Comment(token=token, is_standalone=is_standalone)
        self.comment_buffer.append(comment)

    def _handle_newline(self, token: Token) -> None:
        node = Node.from_token(token=token, previous_node=self.previous_node)
        if self.node_buffer:
            self.node_buffer.append(node)
            self.line_buffer.append(
                Line.from_nodes(
                    source_string="",
                    previous_node=self.previous_line_node,
                    nodes=self.node_buffer,
                    comments=self.comment_buffer,
                )
            )
            self.flush_buffers()
            self.previous_line_node = node
        elif not self.comment_buffer:
            self.line_buffer.append(
                Line.from_nodes(
                    source_string="",
                    previous_node=self.previous_line_node,
                    nodes=[node],
                    comments=[],
                )
            )
            self.previous_line_node = node
        else:
            # standalone comments; don't create a line, since
            # these need to be attached to the next line with
            # contents
            pass
        self.previous_node = node

    def _handle_token(self, token: Token) -> None:
        node = Node.from_token(token=token, previous_node=self.previous_node)
        self.node_buffer.append(node)
        self.previous_node = node

    def lex_old(self, source_string: str, pos: int) -> Iterable[Token]:
        """
        Generate tokens by matching the head of the passed string,
        and then moving the pointer to the head and repeating on
        the rest of the string
        """
        eof_pos = -1
        for idx, char in enumerate(reversed(source_string)):
            if not char.isspace():
                eof_pos = len(source_string) - idx
                break

        while pos < eof_pos:

            for token_type, prog in self.programs.items():

                match = prog.match(source_string, pos)
                if match:
                    spos, epos = match.span(1)
                    prefix = source_string[pos:spos]
                    raw_token = source_string[spos:epos]
                    if token_type in (TokenType.JINJA_END, TokenType.COMMENT_END):
                        raise SqlfmtMultilineError(
                            f"Encountered closing bracket '{raw_token}' at position"
                            f" {spos}, before matching opening bracket:"
                            f" {source_string[spos:spos+50]}"
                        )
                    elif token_type in (
                        TokenType.JINJA_START,
                        TokenType.COMMENT_START,
                    ):
                        # search for the ending token, and/or nest levels deeper
                        epos = self.search_for_terminating_token(
                            start_type=token_type,
                            tail=source_string[epos:],
                            pos=epos,
                        )
                        token = source_string[spos:epos]
                        if token_type == TokenType.JINJA_START:
                            token_type = TokenType.JINJA
                        else:
                            token_type = TokenType.COMMENT
                    else:
                        token = raw_token

                    assert (
                        epos > 0
                    ), "Internal Error! Something went wrong with jinja parsing"

                    yield Token(token_type, prefix, token, pos, epos)

                    pos = epos
                    break
            # nothing matched. Either whitespace or an error
            else:
                raise SqlfmtParsingError(
                    f"Could not parse SQL at position {pos}:"
                    f" '{source_string[pos:pos+50].strip()}'"
                )

    def search_for_terminating_token(
        self, start_type: TokenType, tail: str, pos: int
    ) -> int:
        """
        Return the ending position of the correct closing bracket that matches
        start_type
        """
        terminations = {
            TokenType.JINJA_START: TokenType.JINJA_END,
            TokenType.COMMENT_START: TokenType.COMMENT_END,
        }
        sentinel = terminations[start_type]

        patterns = [self.patterns[t] for t in [start_type, sentinel]]
        prog = re.compile(
            MAYBE_WHITESPACES + group(*patterns), re.IGNORECASE | re.DOTALL
        )

        match = prog.search(tail)
        if not match:
            raise SqlfmtMultilineError(
                f"Unterminated multiline token '{start_type}' "
                f"started near position {pos}. Expecting {sentinel}"
            )

        start, end = match.span(1)

        nesting_prog = self.programs[start_type]
        nesting_match = nesting_prog.match(tail, start)
        if nesting_match:
            inner_epos = self.search_for_terminating_token(
                start_type=start_type,
                tail=tail[end:],
                pos=pos + end,
            )
            outer_epos = self.search_for_terminating_token(
                start_type=start_type,
                tail=tail[inner_epos - pos :],
                pos=inner_epos,
            )
            return outer_epos
        else:
            return pos + end
