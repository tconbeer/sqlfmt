import re
from dataclasses import dataclass
from typing import Dict, Iterable, List

from sqlfmt.dialect import MAYBE_WHITESPACES, SqlfmtParsingError, group
from sqlfmt.exception import SqlfmtError
from sqlfmt.line import Node
from sqlfmt.mode import Mode
from sqlfmt.token import Token, TokenType


class SqlfmtMultilineError(SqlfmtError):
    pass


@dataclass
class Query:
    source_string: str
    mode: Mode
    root: Node

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
        root = Node.create_root()
        q = Query(source_string, mode, root)

        previous_node = root
        for token in q.lex(source_string=source_string, pos=0):
            node = Node.from_token(token, previous_node=previous_node)
            previous_node = node
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
        for node in self.nodes:
            tokens.append(node.token)
        return tokens

    @property
    def nodes(self) -> List[Node]:
        nodes = list(self.root.traverse_children())
        return nodes

    def __str__(self) -> str:
        # todo: pretty printing
        return "".join([str(n) for n in self.nodes]) + "\n"
