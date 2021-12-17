import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional

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


@dataclass
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
    line_length: int
    rules: List[Rule]
    node_buffer: List[Node] = field(default_factory=list)
    comment_buffer: List[Comment] = field(default_factory=list)
    line_buffer: List[Line] = field(default_factory=list)
    previous_node: Optional[Node] = None
    previous_line_node: Optional[Node] = None

    def __post_init__(self) -> None:
        self.patterns = {rule.name: rule.pattern for rule in self.rules}
        self.programs = {rule.name: rule.program for rule in self.rules}

    def write_buffers_to_query(self, query: Query) -> None:
        """
        Write the contents of self.line_buffer to query.lines,
        taking care to flush node_buffer and comment_buffer first
        """
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
        query.lines = self.line_buffer

    def parse_query(self, source_string: str) -> Query:
        """
        Initialize a parser and parse the source string, return
        a structured Query.
        """
        q = Query(source_string, line_length=self.line_length)

        self.lex(source_string=source_string)
        self.write_buffers_to_query(q)
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
            self.node_buffer = []
            self.comment_buffer = []
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

    def lex(self, source_string: str) -> None:
        """
        Repeatedly match Rules to the source_string (until the source_string) is
        exhausted) and apply the matched action.

        Mutates the analyzer's buffers
        """
        pos = 0
        eof_pos = -1
        for idx, char in enumerate(reversed(source_string)):
            if not char.isspace():
                eof_pos = len(source_string) - idx
                break

        while pos < eof_pos:

            for rule in self.rules:

                match = rule.program.match(source_string, pos)
                if match:
                    spos, epos = match.span(1)
                    prefix = source_string[pos:spos]
                    raw_token = source_string[spos:epos]
                    token_type = rule.action(source_string, match)
                    if token_type in (
                        TokenType.JINJA_START,
                        TokenType.COMMENT_START,
                    ):
                        # search for the ending token, and/or nest levels deeper
                        epos = self.search_for_terminating_token(
                            start_rule=rule.name,
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

                    new_token = Token(token_type, prefix, token, pos, epos)
                    if token_type in (TokenType.COMMENT, TokenType.JINJA_COMMENT):
                        self._handle_comment(new_token)
                    elif token_type == TokenType.NEWLINE:
                        self._handle_newline(new_token)
                    else:
                        self._handle_token(new_token)

                    pos = epos
                    break
            # nothing matched. Either whitespace or an error
            else:
                raise SqlfmtParsingError(
                    f"Could not parse SQL at position {pos}:"
                    f" '{source_string[pos:pos+50].strip()}'"
                )

    def search_for_terminating_token(self, start_rule: str, tail: str, pos: int) -> int:
        """
        Return the ending position of the correct closing bracket that matches
        start_type
        """
        terminations = {
            "jinja_start": "jinja_end",
            "comment_start": "comment_end",
        }
        sentinel = terminations[start_rule]

        patterns = [self.patterns[t] for t in [start_rule, sentinel]]
        prog = re.compile(
            MAYBE_WHITESPACES + group(*patterns), re.IGNORECASE | re.DOTALL
        )

        match = prog.search(tail)
        if not match:
            raise SqlfmtMultilineError(
                f"Unterminated multiline token '{start_rule}' "
                f"started near position {pos}. Expecting {sentinel}"
            )

        start, end = match.span(1)

        nesting_prog = self.programs[start_rule]
        nesting_match = nesting_prog.match(tail, start)
        if nesting_match:
            inner_epos = self.search_for_terminating_token(
                start_rule=start_rule,
                tail=tail[end:],
                pos=pos + end,
            )
            outer_epos = self.search_for_terminating_token(
                start_rule=start_rule,
                tail=tail[inner_epos - pos :],
                pos=inner_epos,
            )
            return outer_epos
        else:
            return pos + end
