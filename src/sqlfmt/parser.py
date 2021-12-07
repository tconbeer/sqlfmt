import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from sqlfmt.dialect import MAYBE_WHITESPACES, SqlfmtParsingError, group
from sqlfmt.exception import SqlfmtError
from sqlfmt.line import Comment, Line, Node
from sqlfmt.mode import Mode
from sqlfmt.token import Token, TokenType


class SqlfmtMultilineError(SqlfmtError):
    pass


@dataclass
class Query:
    source_string: str
    mode: Mode
    lines: List[Line] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.PATTERNS = self.mode.dialect.get_patterns()
        self.programs: Dict[TokenType, re.Pattern] = {
            k: re.compile(MAYBE_WHITESPACES + v, re.IGNORECASE | re.DOTALL)
            for k, v in self.PATTERNS.items()
        }

    @classmethod
    def from_source(cls, source_string: str, mode: Mode) -> "Query":
        """
        Initialize a parser and parse the source string.
        """
        q = Query(source_string, mode)

        previous_node: Optional[Node] = None
        previous_line_node: Optional[Node] = None
        line_nodes: List[Node] = []
        line_comments: List[Comment] = []
        for token in q.lex(source_string=source_string, pos=0):
            if token.type in (TokenType.COMMENT, TokenType.JINJA_COMMENT):
                is_standalone = (not bool(line_nodes)) or "\n" in token.token
                comment = Comment(token=token, is_standalone=is_standalone)
                line_comments.append(comment)
            else:
                node = Node.from_token(token=token, previous_node=previous_node)
                if node.is_newline and line_nodes:
                    line_nodes.append(node)
                    q.lines.append(
                        Line.from_nodes(
                            source_string="",
                            previous_node=previous_line_node,
                            nodes=line_nodes,
                            comments=line_comments,
                        )
                    )
                    line_nodes = []
                    line_comments = []
                    previous_line_node = node
                elif node.is_newline and not line_comments:
                    q.lines.append(
                        Line.from_nodes(
                            source_string="",
                            previous_node=previous_line_node,
                            nodes=[node],
                            comments=[],
                        )
                    )
                    previous_line_node = node
                elif node.is_newline and line_comments:
                    # standalone comments; don't create a line, since
                    # these need to be attached to the next line with
                    # contents
                    pass
                else:
                    line_nodes.append(node)
                previous_node = node
        # append a final line if the file doesn't end with a newline
        if line_nodes:
            line = Line.from_nodes(
                source_string="",
                previous_node=previous_line_node,
                nodes=line_nodes,
                comments=line_comments,
            )
            line.append_newline()
            q.lines.append(line)
        return q

    def lex(self, source_string: str, pos: int) -> Iterable[Token]:
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

        patterns = [self.PATTERNS[t] for t in [start_type, sentinel]]
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

    def __str__(self) -> str:
        draft = [
            line.render_with_comments(self.mode.line_length) for line in self.lines
        ]
        return "".join(draft)
