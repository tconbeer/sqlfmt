import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from sqlfmt.dialect import MAYBE_WHITESPACES, SqlfmtParsingError, group
from sqlfmt.exception import SqlfmtError
from sqlfmt.line import Line, Node
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
        line = Line(source_string=source_string, previous_node=None)
        q.lines.append(line)
        for token in q.lex(tail=q.source_string, pos=0):
            line.append_token(token)
        return q

    def lex(self, tail: str, pos: int) -> Iterable[Token]:
        """
        Generate tokens by matching the head of the passed string,
        and then recursing on the tail
        """
        if tail.strip() == "":
            return
        else:
            for token_type, prog in self.programs.items():

                match = prog.match(tail)
                if match:
                    spos = pos
                    start, end = match.span(1)
                    raw_prefix = tail[:start]
                    prefix = raw_prefix.replace("\n", " ")
                    raw_token = tail[start:end]
                    if token_type in (TokenType.JINJA_END, TokenType.COMMENT_END):
                        raise SqlfmtMultilineError(
                            f"Encountered closing bracket '{raw_token}' at position "
                            f"{pos+start}, before matching opening bracket: "
                            f"{tail[start:start+50]}"
                        )
                    elif token_type in (TokenType.JINJA_START, TokenType.COMMENT_START):
                        # search for the ending token, and/or nest levels deeper
                        epos = self.search_for_terminating_token(
                            start_type=token_type,
                            tail=tail[end:],
                            pos=pos + end,
                        )
                        end = epos - pos
                        token = tail[start:end].strip()
                        if token_type == TokenType.JINJA_START:
                            token_type = TokenType.JINJA
                        else:
                            token_type = TokenType.COMMENT
                    else:
                        epos = pos + end
                        if token_type in (
                            TokenType.COMMENT,
                            TokenType.FMT_OFF,
                            TokenType.FMT_ON,
                            TokenType.JINJA,
                        ):
                            token = raw_token.strip()
                        else:
                            token = raw_token.replace("\n", " ").strip()

                    yield Token(token_type, prefix, token, spos, epos)
                    break
            # nothing matched. Either whitespace or an error
            else:
                raise SqlfmtParsingError(
                    f"Could not parse SQL at position {pos}:"
                    f" '{tail[pos:pos+50].strip()}'"
                )
            yield from self.lex(tail=tail[end:], pos=epos)

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
        draft = []
        for s in [str(line) for line in self.lines]:
            if s:
                draft.append(s)

        q = "".join(draft)
        return q
