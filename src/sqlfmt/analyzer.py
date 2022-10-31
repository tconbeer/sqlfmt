import re
from dataclasses import dataclass, field
from typing import List, Optional

from sqlfmt.comment import Comment
from sqlfmt.exception import SqlfmtBracketError, SqlfmtParsingError
from sqlfmt.line import Line
from sqlfmt.node import Node
from sqlfmt.node_manager import NodeManager
from sqlfmt.query import Query
from sqlfmt.rule import Rule


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
    node_manager: NodeManager
    node_buffer: List[Node] = field(default_factory=list)
    comment_buffer: List[Comment] = field(default_factory=list)
    line_buffer: List[Line] = field(default_factory=list)
    rule_stack: List[List[Rule]] = field(default_factory=list)
    pos: int = 0

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
        """
        Reset the analyer's node, comment, and line buffers, and its parsing position.
        (It is possible for the same analyzer to be used to lex twice, so we need to
        reset buffers before lexing begins)
        """
        self.node_buffer = []
        self.comment_buffer = []
        self.line_buffer = []
        self.pos = 0

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
            self.node_manager.append_newline(line)
            self.line_buffer.append(line)

        # if the final line(s) are jinja block end tags, they may be
        # indented too far -- they should be formatted as if they
        # have no open_brackets
        for line in reversed(self.line_buffer):
            if line.closes_jinja_block_from_previous_line:
                for node in line.nodes:
                    node.open_brackets = []
            else:
                break
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

    def push_rules(self, new_rules: List[Rule]) -> None:
        self.rule_stack.append(self.rules.copy())
        self.rules = sorted(new_rules, key=lambda rule: rule.priority)

    def pop_rules(self) -> List[Rule]:
        old_rules = self.rules
        self.rules = self.rule_stack.pop()
        return old_rules

    def get_rule(self, rule_name: str) -> Rule:
        """
        Return the rule from ruleset that matches rule_name
        """
        matching_rules = filter(lambda rule: rule.name == rule_name, self.rules)
        try:
            return next(matching_rules)
        except StopIteration:
            raise ValueError(f"No rule '{rule_name}'")

    def lex_one(self, source_string: str) -> None:
        """
        Repeatedly match Rules to the source_string (at self.pos)
        and apply the matched action.

        Mutates the analyzer's buffers and pos
        """
        for rule in self.rules:
            match = rule.program.match(source_string, self.pos)
            if match:
                rule.action(self, source_string, match)
                return
        # nothing matched. Either whitespace or an error
        else:
            raise SqlfmtParsingError(
                f"Could not parse SQL at position {self.pos}:"
                f" '{source_string[self.pos:self.pos+50].strip()}'"
            )

    def lex(self, source_string: str, eof_pos: int = -1) -> None:
        """
        Repeatedly match Rules to the source_string (until the source_string is
        exhausted) and apply the matched action.

        Mutates the analyzer's buffers
        """
        if eof_pos == -1:
            for idx, char in enumerate(reversed(source_string)):
                if not char.isspace():
                    eof_pos = len(source_string) - idx
                    break

        last_loop_pos = -1
        while self.pos < eof_pos and self.pos > last_loop_pos:
            last_loop_pos = self.pos
            self.lex_one(source_string)

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
            raise SqlfmtBracketError(
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
