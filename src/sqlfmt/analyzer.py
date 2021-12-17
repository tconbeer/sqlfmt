import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from sqlfmt.exception import SqlfmtError, SqlfmtMultilineError
from sqlfmt.line import Comment, Line, Node
from sqlfmt.query import Query


class SqlfmtParsingError(SqlfmtError):
    pass


@dataclass
class Rule:
    """
    A lex rule.

    When the analyzer lexes the source string, it applies each Rule in turn,
    in ascending order of priority.

    The Analyzer tries to match the Rule's regex pattern to the current position
    in the source string. If there is a match, the Analyzer calls the Rule's
    action with the arguments (self [the analyzer], source_string, match). The
    Rule's action may mutate the analyzer's buffer (if desired). The action
    must return the position in the source_string where the Analyzer should
    look for the next match.
    """

    name: str
    priority: int  # lower get matched first
    pattern: str
    action: Callable[["Analyzer", str, re.Match], int]

    def __post_init__(self) -> None:
        MAYBE_WHITESPACES = r"[^\S\n]*"  # any whitespace except newline
        self.program = re.compile(
            MAYBE_WHITESPACES + self.pattern, re.IGNORECASE | re.DOTALL
        )


@dataclass
class Analyzer:
    """
    The Analyzer is initialized by the dialect specified by the user. The
    dialect specifies the list of rules that the Analyzer will attempt
    to match to the source string during parsing. The analyzer maintains
    buffers of lexed nodes, comments, and lines.
    """

    line_length: int
    rules: List[Rule]
    node_buffer: List[Node] = field(default_factory=list)
    comment_buffer: List[Comment] = field(default_factory=list)
    line_buffer: List[Line] = field(default_factory=list)

    @property
    def previous_node(self) -> Optional[Node]:
        """
        Return the most recently-lexed Node, if it exists
        """
        if self.node_buffer:
            return self.node_buffer[-1]
        else:
            return self.previous_line_node

    @property
    def previous_line_node(self) -> Optional[Node]:
        """
        Return the last node of the last complete line
        """
        if self.line_buffer:
            return self.line_buffer[-1].nodes[-1]
        else:
            return None

    def clear_buffers(self) -> None:
        self.node_buffer = []
        self.comment_buffer = []
        self.line_buffer = []

    def write_buffers_to_query(self, query: Query) -> None:
        """
        Write the contents of self.line_buffer to query.lines,
        taking care to flush node_buffer and comment_buffer first
        """
        # append a final line if the file doesn't end with a newline
        if self.node_buffer or self.comment_buffer:
            line = Line.from_nodes(
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

        self.clear_buffers()
        self.lex(source_string=source_string)
        self.write_buffers_to_query(q)
        return q

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
                    epos = rule.action(self, source_string, match)
                    pos = epos
                    break
            # nothing matched. Either whitespace or an error
            else:
                raise SqlfmtParsingError(
                    f"Could not parse SQL at position {pos}:"
                    f" '{source_string[pos:pos+50].strip()}'"
                )

    def search_for_terminating_token(
        self,
        start_rule: str,
        program: re.Pattern,
        nesting_program: re.Pattern,
        tail: str,
        pos: int,
    ) -> int:
        """
        Return the ending position of the correct closing bracket that matches
        start_rule
        """

        match = program.search(tail)
        if not match:
            raise SqlfmtMultilineError(
                f"Unterminated multiline token '{start_rule}' "
                f"started near position {pos}."
            )

        start, end = match.span(1)

        nesting_match = nesting_program.match(tail, start)
        if nesting_match:
            inner_epos = self.search_for_terminating_token(
                start_rule=start_rule,
                program=program,
                nesting_program=nesting_program,
                tail=tail[end:],
                pos=pos + end,
            )
            outer_epos = self.search_for_terminating_token(
                start_rule=start_rule,
                program=program,
                nesting_program=nesting_program,
                tail=tail[inner_epos - pos :],
                pos=inner_epos,
            )
            return outer_epos
        else:
            return pos + end
