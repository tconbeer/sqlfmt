import re
from abc import ABC, abstractmethod
from functools import partial
from typing import List

from sqlfmt.analyzer import Analyzer, Rule
from sqlfmt.exception import SqlfmtMultilineError
from sqlfmt.line import Comment, Line, Node
from sqlfmt.token import Token, TokenType


def group(*choices: str) -> str:
    return "(" + "|".join(choices) + ")"


WHITESPACE: str = r"\s"
WHITESPACES: str = WHITESPACE + "+"
MAYBE_WHITESPACES: str = r"[^\S\n]*"  # any whitespace except newline
NEWLINE: str = r"\r?\n"
ANY_BLANK: str = group(WHITESPACES, r"$")
EOL = group(NEWLINE, r"$")


class Dialect(ABC):
    """
    Abstract class for a SQL dialect.

    Each dialect should override the PATTERNS dict to define their own grammar.
    Each value in the PATTERNS dict must have a regex group (surrounded by
    parentheses) that matches the token; if the token may be delimited by
    whitespace, that should be defined outside the first group.
    """

    RULES: List[Rule]

    @abstractmethod
    def get_rules(self) -> List[Rule]:
        return sorted(self.RULES, key=lambda rule: rule.priority)

    def initialize_analyzer(self, line_length: int) -> Analyzer:
        analyzer = Analyzer(
            line_length=line_length,
            rules=sorted(self.RULES, key=lambda rule: rule.priority),
        )
        return analyzer


class Polyglot(Dialect):
    """
    A universal SQL dialect meant to encompass the common usage of at least
    Postgres, MySQL, BigQuery Standard SQL, Snowflake SQL, SparkSQL.
    """

    def __init__(self) -> None:
        self.RULES: List[Rule] = [
            Rule(
                name="fmt_off",
                priority=0,
                pattern=group(r"(--|#) ?fmt: ?off ?") + EOL,
                action=partial(self.add_node_to_buffer, token_type=TokenType.FMT_OFF),
            ),
            Rule(
                name="fmt_on",
                priority=1,
                pattern=group(r"(--|#) ?fmt: ?on ?") + EOL,
                action=partial(self.add_node_to_buffer, token_type=TokenType.FMT_ON),
            ),
            # these only match simple jinja tags, without nesting or potential nesting
            Rule(
                name="jinja_comment",
                priority=100,
                pattern=group(r"\{\#.*?\#\}"),
                action=self.add_comment_to_buffer,
            ),
            Rule(
                name="jinja",
                priority=110,
                pattern=group(
                    r"\{\{[^{}%#]*\}\}",
                    r"\{%[^{}%#]*?%\}",
                ),
                action=partial(self.add_node_to_buffer, token_type=TokenType.JINJA),
            ),
            # These match just the start and end of jinja tags, which allows
            # the parser to deal with nesting in a more powerful way than
            # regex allows
            Rule(
                name="jinja_start",
                priority=120,
                pattern=group(r"\{[{%]"),
                action=partial(self.handle_complex_tokens, rule_name="jinja_start"),
            ),
            Rule(
                name="jinja_end",
                priority=130,
                pattern=group(r"[}%]\}"),
                action=self.raise_sqlfmt_multiline_error,
            ),
            Rule(
                name="quoted_name",
                priority=200,
                pattern=group(
                    # tripled single quotes (optionally raw/bytes)
                    r"(rb?|b|br)?'''.*?'''",
                    # tripled double quotes
                    r'(rb?|b|br)?""".*?"""',
                    # possibly escaped double quotes
                    r'(rb?|b|br|u&)?"([^"\\]*(\\.[^"\\]*|""[^"\\]*)*)"',
                    # possibly escaped single quotes
                    r"(rb?|b|br|u&|x)?'([^'\\]*(\\.[^'\\]*|''[^'\\]*)*)'",
                    r"\$\w*\$[^$]*?\$\w*\$",  # pg dollar-delimited strings
                    # possibly escaped backtick
                    r"`([^`\\]*(\\.[^`\\]*)*)`",
                ),
                action=partial(
                    self.add_node_to_buffer, token_type=TokenType.QUOTED_NAME
                ),
            ),
            Rule(
                name="comment",
                priority=300,
                pattern=group(
                    r"--[^\r\n]*",
                    r"#[^\r\n]*",
                    r"/\*[^*]*\*+(?:[^/*][^*]*\*+)*/",  # simple block comment
                ),
                action=self.add_comment_to_buffer,
            ),
            Rule(
                name="comment_start",
                priority=310,
                pattern=group(r"/\*"),
                action=partial(self.handle_complex_tokens, rule_name="comment_start"),
            ),
            Rule(
                name="comment_end",
                priority=320,
                pattern=group(r"\*/"),
                action=self.raise_sqlfmt_multiline_error,
            ),
            Rule(
                name="semicolon",
                priority=400,
                pattern=group(r";"),
                action=partial(self.add_node_to_buffer, token_type=TokenType.SEMICOLON),
            ),
            Rule(
                name="statement_start",
                priority=500,
                pattern=group(r"case") + group(r"\W", r"$"),
                action=partial(
                    self.add_node_to_buffer, token_type=TokenType.STATEMENT_START
                ),
            ),
            Rule(
                name="statement_end",
                priority=510,
                pattern=group(r"end") + group(r"\W", r"$"),
                action=partial(
                    self.add_node_to_buffer, token_type=TokenType.STATEMENT_END
                ),
            ),
            Rule(
                name="star",
                priority=600,
                pattern=group(r"\*"),
                action=partial(self.add_node_to_buffer, token_type=TokenType.STAR),
            ),
            Rule(
                name="number",
                priority=700,
                pattern=group(
                    r"-?\d+\.?\d*",
                    r"-?\.\d+",
                ),
                action=partial(self.add_node_to_buffer, token_type=TokenType.NUMBER),
            ),
            Rule(
                name="bracket_open",
                priority=800,
                pattern=group(
                    r"\[",
                    r"\(",
                    r"\{",
                ),
                action=partial(
                    self.add_node_to_buffer, token_type=TokenType.BRACKET_OPEN
                ),
            ),
            Rule(
                name="bracket_close",
                priority=810,
                pattern=group(
                    r"\]",
                    r"\)",
                    r"\}",
                ),
                action=partial(
                    self.add_node_to_buffer, token_type=TokenType.BRACKET_CLOSE
                ),
            ),
            Rule(
                name="double_colon",
                priority=900,
                pattern=group(r"::"),
                action=partial(
                    self.add_node_to_buffer, token_type=TokenType.DOUBLE_COLON
                ),
            ),
            Rule(
                name="operator",
                priority=910,
                pattern=group(
                    r"<>",
                    r"!=",
                    r"\|\|",
                    r"[+\-*/%&@|^=<>:]=?",
                    r"~",
                ),
                action=partial(self.add_node_to_buffer, token_type=TokenType.OPERATOR),
            ),
            Rule(
                name="word_operator",
                priority=920,
                pattern=group(
                    r"between",
                    r"ilike",
                    r"in",
                    r"is",
                    r"isnull",
                    r"like",
                    r"not",
                    r"notnull",
                    r"over",
                    r"similar",
                )
                + group(r"\W", r"$"),
                action=partial(
                    self.add_node_to_buffer, token_type=TokenType.WORD_OPERATOR
                ),
            ),
            Rule(
                name="as",
                priority=930,
                pattern=group(r"as") + group(r"\W", r"$"),
                action=partial(self.add_node_to_buffer, token_type=TokenType.AS),
            ),
            Rule(
                name="on",
                priority=940,
                pattern=group(r"on") + group(r"\W", r"$"),
                action=partial(self.add_node_to_buffer, token_type=TokenType.ON),
            ),
            Rule(
                name="boolean_operator",
                priority=950,
                pattern=group(
                    r"and",
                    r"or",
                    r"on",
                    r"as",
                )
                + group(r"\W", r"$"),
                action=partial(
                    self.add_node_to_buffer, token_type=TokenType.BOOLEAN_OPERATOR
                ),
            ),
            Rule(
                name="comma",
                priority=960,
                pattern=group(r","),
                action=partial(self.add_node_to_buffer, token_type=TokenType.COMMA),
            ),
            Rule(
                name="dot",
                priority=970,
                pattern=group(r"\."),
                action=partial(self.add_node_to_buffer, token_type=TokenType.DOT),
            ),
            Rule(
                name="unterm_keyword",
                priority=1000,
                pattern=group(
                    r"with(\s+recursive)?",
                    (
                        r"select(\s+(as\s+struct|as\s+value))?"
                        r"(\s+(all|top\s+\d+|distinct))?"
                    ),
                    r"from",
                    r"(natural\s+)?((inner|((left|right|full)(\s+outer)?))\s+)?join",
                    r"where",
                    r"group\s+by",
                    r"having",
                    r"qualify",
                    r"window",
                    r"(union|intersect|except)(\s+all|distinct)?",
                    r"order\s+by",
                    r"limit",
                    r"offset",
                    r"fetch\s+(first|next)",
                    r"for\s+(update|no\s+key\s+update|share|key\s+share)",
                    r"when",
                    r"then",
                    r"else",
                    r"partition\s+by",
                    r"rows\s+between",
                )
                + group(r"\W", r"$"),
                action=partial(
                    self.add_node_to_buffer, token_type=TokenType.UNTERM_KEYWORD
                ),
            ),
            Rule(
                name="name",
                priority=5000,
                pattern=group(r"\w+"),
                action=partial(self.add_node_to_buffer, token_type=TokenType.NAME),
            ),
            Rule(
                name="newline",
                priority=9000,
                pattern=group(NEWLINE),
                action=self.handle_newline,
            ),
        ]

    def get_rules(self) -> List[Rule]:
        return super().get_rules()

    @staticmethod
    def raise_sqlfmt_multiline_error(
        _: Analyzer, source_string: str, match: re.Match
    ) -> int:
        spos, epos = match.span(1)
        raw_token = source_string[spos:epos]
        raise SqlfmtMultilineError(
            f"Encountered closing bracket '{raw_token}' at position"
            f" {spos}, before matching opening bracket:"
            f" {source_string[spos:spos+50]}"
        )

    @staticmethod
    def add_node_to_buffer(
        analyzer: Analyzer,
        source_string: str,
        match: re.Match,
        token_type: TokenType,
    ) -> int:
        token = Token.from_match(source_string, match, token_type)
        node = Node.from_token(token=token, previous_node=analyzer.previous_node)
        analyzer.node_buffer.append(node)
        analyzer.previous_node = node
        return token.epos

    @staticmethod
    def add_comment_to_buffer(
        analyzer: Analyzer,
        source_string: str,
        match: re.Match,
    ) -> int:
        token = Token.from_match(source_string, match, TokenType.COMMENT)
        is_standalone = (not bool(analyzer.node_buffer)) or "\n" in token.token
        comment = Comment(token=token, is_standalone=is_standalone)
        analyzer.comment_buffer.append(comment)
        return token.epos

    @staticmethod
    def handle_newline(
        analyzer: Analyzer,
        source_string: str,
        match: re.Match,
    ) -> int:
        token = Token.from_match(source_string, match, TokenType.NEWLINE)
        node = Node.from_token(token=token, previous_node=analyzer.previous_node)
        if analyzer.node_buffer:
            analyzer.node_buffer.append(node)
            analyzer.line_buffer.append(
                Line.from_nodes(
                    source_string="",
                    previous_node=analyzer.previous_line_node,
                    nodes=analyzer.node_buffer,
                    comments=analyzer.comment_buffer,
                )
            )
            analyzer.node_buffer = []
            analyzer.comment_buffer = []
            analyzer.previous_line_node = node
        elif not analyzer.comment_buffer:
            analyzer.line_buffer.append(
                Line.from_nodes(
                    source_string="",
                    previous_node=analyzer.previous_line_node,
                    nodes=[node],
                    comments=[],
                )
            )
            analyzer.previous_line_node = node
        else:
            # standalone comments; don't create a line, since
            # these need to be attached to the next line with
            # contents
            pass
        analyzer.previous_node = node
        return token.epos

    @staticmethod
    def handle_complex_tokens(
        analyzer: Analyzer,
        source_string: str,
        match: re.Match,
        rule_name: str,
    ) -> int:
        pass
        pos, _ = match.span(0)
        spos, epos = match.span(1)
        prefix = source_string[pos:spos]
        # search for the ending token, and/or nest levels deeper
        epos = analyzer.search_for_terminating_token(
            start_rule=rule_name,
            tail=source_string[epos:],
            pos=epos,
        )
        token = source_string[spos:epos]
        if rule_name == "jinja_start":
            token_type = TokenType.JINJA
            new_token = Token(token_type, prefix, token, pos, epos)
            node = Node.from_token(new_token, analyzer.previous_node)
            analyzer.node_buffer.append(node)
            analyzer.previous_node = node
        else:
            token_type = TokenType.COMMENT
            new_token = Token(token_type, prefix, token, pos, epos)
            is_standalone = (not bool(analyzer.node_buffer)) or "\n" in new_token.token
            comment = Comment(token=new_token, is_standalone=is_standalone)
            analyzer.comment_buffer.append(comment)
        return epos
