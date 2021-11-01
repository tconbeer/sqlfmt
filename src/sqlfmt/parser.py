from dataclasses import dataclass, field
from io import StringIO
from typing import Iterator, List, Optional, Tuple

from sqlfmt.dialect import Dialect
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

    @classmethod
    def from_source(cls, source_string: str, mode: Mode) -> "Query":
        """
        Initialize a parser and parse the source string.
        """
        q = Query(source_string, mode)
        q.tokenize_from_source()
        return q

    def tokenize_from_source(self) -> None:
        """
        Updates self.lines by lexing source_string into tokens. Supports multiline
        tokens by initializing a MultilineConsumer.
        """
        if not self.source_string:
            return

        if self.lines and self.tokens:
            # don't run this again
            return

        buffer = StringIO(self.source_string)
        reader = enumerate(buffer.readlines())

        for lnum, line in reader:
            current_line = Line(
                source_string=line,
                previous_node=self.lines[-1].nodes[-1] if self.lines else None,
            )
            for token in self.mode.dialect.tokenize_line(line=line, lnum=lnum):
                # most tokens are contained on a single line. However, for multiline
                # comments and jinja tags, tokenize_line only returns the opening
                # bracket; we need to scan ahead to find the ending bracket
                if MultilineConsumer.is_multiline_end_token(token):
                    raise SqlfmtMultilineError(
                        f"Encountered multiline end token '{token.token}' at "
                        f"{token.spos}, before matching multiline start token"
                    )
                if MultilineConsumer.is_multiline_start_token(token):
                    mc = MultilineConsumer(
                        reader, dialect=self.mode.dialect, start=token, source=[line]
                    )
                    current_line.append_token(mc.multiline_token)

                    # if there are additional tokens trailing a multiline
                    # comment, we want to put those on their own logical Line,
                    # so they are properly split
                    trailing_tokens: List[Token] = mc.trailing_tokens
                    if (
                        trailing_tokens
                        and current_line.nodes
                        and mc.multiline_token.type == TokenType.COMMENT
                    ):
                        current_line.append_newline()
                        self.lines.append(current_line)
                        current_line = Line(
                            source_string=mc.source[-1],
                            previous_node=self.lines[-1].nodes[-1]
                            if self.lines
                            else None,
                        )
                    for t in trailing_tokens:
                        current_line.append_token(t)

                    current_line.append_newline()
                    break

                # just a simple token
                else:
                    current_line.append_token(token)

            if current_line.nodes:
                current_line.maybe_append_newline()
                self.lines.append(current_line)

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


@dataclass
class MultilineConsumer:
    """
    We need to track some state in order to properly parse multiline tokens,
    especially since they can be nested in some circumstances. This class
    holds that state. It is initialized by the parser when a token is
    encountered that indicates the start of a multiline token, and/or
    when it scans for the end of the multiline token and must recurse
    to handle nested comments or jinja tags. Once initialized, scan_to_end
    does most of the hard work, but clients can just call the multiline_token
    property. This class consumes the same string buffer as its caller,
    so when it returns, the caller needs to proceed to the next line.
    """

    reader: Iterator[Tuple[int, str]]
    dialect: Dialect
    start: Token
    source: List[str]
    end: Optional[Token] = None

    def scan_to_end(self) -> None:
        """
        Sets self.end by consuming self.reader and looking for a token that
        matches the terminating token for self.start
        """
        if self.end:
            return
        terminations = {
            TokenType.JINJA_START: TokenType.JINJA_END,
            TokenType.COMMENT_START: TokenType.COMMENT_END,
        }
        sentinel = terminations[self.start.type]
        inline_match = self.dialect.search_for_token(
            token_types=[self.start.type, sentinel],
            line=self.source[-1],
            lnum=self.start.spos[0],
            skipchars=self.start.epos[1],
        )
        if self._handle_match(inline_match, sentinel):
            return

        for lnum, line in self.reader:
            self.source.append(line)
            matching_token = self.dialect.search_for_token(
                token_types=[self.start.type, sentinel], line=line, lnum=lnum
            )
            if self._handle_match(matching_token, sentinel):
                break

        else:  # exhausted reader without finding end token
            raise SqlfmtMultilineError(
                f"Unterminated multiline token '{self.start.token}' "
                f"started at {self.start.spos}"
            )

    def _handle_match(
        self, matching_token: Optional[Token], sentinel: TokenType
    ) -> bool:
        """
        Returns True if end is set from the match; False otherwise.
        """

        if matching_token and matching_token.type == sentinel:
            self.end = matching_token
            return True
        elif matching_token and matching_token.type == self.start.type:
            # nested multiline markers! recurse on the new token to consume
            # reader until we hit the inner sentinel
            mc = MultilineConsumer(
                self.reader,
                self.dialect,
                start=matching_token,
                source=self.source.copy(),
            )
            inner_token = mc.multiline_token
            self.source = [inner_token.line]
            return False
        else:
            return False

    @property
    def multiline_token(self) -> Token:
        """
        Construct a single token that spans the input from the start
        token to end token
        """
        if not self.end:
            self.scan_to_end()

        translations = {
            TokenType.JINJA_START: TokenType.JINJA,
            TokenType.COMMENT_START: TokenType.COMMENT,
        }

        multiline_token = Token(
            type=translations[self.start.type],
            prefix=self.start.prefix,
            token=self.contents,
            spos=self.start.spos,
            epos=self.end.epos,  # type: ignore
            line="".join(self.source),
        )

        return multiline_token

    @property
    def trailing_tokens(self) -> List[Token]:
        """
        A multiline token can have more tokens trailing its end token.
        We collect those and return them as a List, or return [] if
        we only find a NEWLINE
        """
        if not self.end:
            self.scan_to_end()

        token_list: List[Token] = []
        for token in self.dialect.tokenize_line(
            line=self.source[-1],
            lnum=self.end.epos[0],  # type: ignore
            skipchars=self.end.epos[1],  # type: ignore
        ):
            if token.type != TokenType.NEWLINE:
                token_list.append(token)
        return token_list

    @property
    def contents(self) -> str:
        """
        Return a string to be used for Token.token for the multiline
        token. This is mostly the same as the source string, but
        is trimmed at the beginning and end to omit any other tokens
        on the first and last lines, if they exist.
        """
        if not self.end:
            self.scan_to_end()

        contents = self.source.copy()
        if len(contents) > 1:
            contents[0] = contents[0][self.start.spos[1] :]
            contents[-1] = contents[-1][: self.end.epos[1]]  # type: ignore
        else:
            contents[0] = contents[0][
                self.start.spos[1] : self.end.epos[1]  # type: ignore
            ]
        return "".join(contents)

    @classmethod
    def is_multiline_start_token(cls, token: Token) -> bool:
        if token.type in (TokenType.JINJA_START, TokenType.COMMENT_START):
            return True
        else:
            return False

    @classmethod
    def is_multiline_end_token(cls, token: Token) -> bool:
        if token.type in (TokenType.JINJA_END, TokenType.COMMENT_END):
            return True
        else:
            return False
