import re
from abc import ABC, abstractmethod
from typing import List

from sqlfmt.analyzer import Analyzer, Rule
from sqlfmt.exception import SqlfmtMultilineError
from sqlfmt.token import TokenType


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
                action=lambda source_string, match: TokenType.FMT_OFF,
            ),
            Rule(
                name="fmt_on",
                priority=1,
                pattern=group(r"(--|#) ?fmt: ?on ?") + EOL,
                action=lambda source_string, match: TokenType.FMT_ON,
            ),
            # these only match simple jinja tags, without nesting or potential nesting
            Rule(
                name="jinja_comment",
                priority=100,
                pattern=group(r"\{\#.*?\#\}"),
                action=lambda source_string, match: TokenType.JINJA_COMMENT,
            ),
            Rule(
                name="jinja",
                priority=110,
                pattern=group(
                    r"\{\{[^{}%#]*\}\}",
                    r"\{%[^{}%#]*?%\}",
                ),
                action=lambda source_string, match: TokenType.JINJA,
            ),
            # These match just the start and end of jinja tags, which allows
            # the parser to deal with nesting in a more powerful way than
            # regex allows
            Rule(
                name="jinja_start",
                priority=120,
                pattern=group(r"\{[{%]"),
                action=lambda source_string, match: TokenType.JINJA_START,
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
                action=lambda source_string, match: TokenType.QUOTED_NAME,
            ),
            Rule(
                name="comment",
                priority=300,
                pattern=group(
                    r"--[^\r\n]*",
                    r"#[^\r\n]*",
                    r"/\*[^*]*\*+(?:[^/*][^*]*\*+)*/",  # simple block comment
                ),
                action=lambda source_string, match: TokenType.COMMENT,
            ),
            Rule(
                name="comment_start",
                priority=310,
                pattern=group(r"/\*"),
                action=lambda source_string, match: TokenType.COMMENT_START,
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
                action=lambda source_string, match: TokenType.SEMICOLON,
            ),
            Rule(
                name="statement_start",
                priority=500,
                pattern=group(r"case") + group(r"\W", r"$"),
                action=lambda source_string, match: TokenType.STATEMENT_START,
            ),
            Rule(
                name="statement_end",
                priority=510,
                pattern=group(r"end") + group(r"\W", r"$"),
                action=lambda source_string, match: TokenType.STATEMENT_END,
            ),
            Rule(
                name="star",
                priority=600,
                pattern=group(r"\*"),
                action=lambda source_string, match: TokenType.STAR,
            ),
            Rule(
                name="number",
                priority=700,
                pattern=group(
                    r"-?\d+\.?\d*",
                    r"-?\.\d+",
                ),
                action=lambda source_string, match: TokenType.NUMBER,
            ),
            Rule(
                name="bracket_open",
                priority=800,
                pattern=group(
                    r"\[",
                    r"\(",
                    r"\{",
                ),
                action=lambda source_string, match: TokenType.BRACKET_OPEN,
            ),
            Rule(
                name="bracket_close",
                priority=810,
                pattern=group(
                    r"\]",
                    r"\)",
                    r"\}",
                ),
                action=lambda source_string, match: TokenType.BRACKET_CLOSE,
            ),
            Rule(
                name="double_colon",
                priority=900,
                pattern=group(r"::"),
                action=lambda source_string, match: TokenType.DOUBLE_COLON,
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
                action=lambda source_string, match: TokenType.OPERATOR,
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
                action=lambda source_string, match: TokenType.WORD_OPERATOR,
            ),
            Rule(
                name="as",
                priority=930,
                pattern=group(r"as") + group(r"\W", r"$"),
                action=lambda source_string, match: TokenType.AS,
            ),
            Rule(
                name="on",
                priority=940,
                pattern=group(r"on") + group(r"\W", r"$"),
                action=lambda source_string, match: TokenType.ON,
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
                action=lambda source_string, match: TokenType.BOOLEAN_OPERATOR,
            ),
            Rule(
                name="comma",
                priority=960,
                pattern=group(r","),
                action=lambda source_string, match: TokenType.COMMA,
            ),
            Rule(
                name="dot",
                priority=970,
                pattern=group(r"\."),
                action=lambda source_string, match: TokenType.DOT,
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
                action=lambda source_string, match: TokenType.UNTERM_KEYWORD,
            ),
            Rule(
                name="name",
                priority=5000,
                pattern=group(r"\w+"),
                action=lambda source_string, match: TokenType.NAME,
            ),
            Rule(
                name="newline",
                priority=9000,
                pattern=group(NEWLINE),
                action=lambda source_string, match: TokenType.NEWLINE,
            ),
        ]

    def get_rules(self) -> List[Rule]:
        return super().get_rules()

    def raise_sqlfmt_multiline_error(self, source_string: str, match: re.Match) -> None:
        spos, epos = match.span(1)
        raw_token = source_string[spos:epos]
        raise SqlfmtMultilineError(
            f"Encountered closing bracket '{raw_token}' at position"
            f" {spos}, before matching opening bracket:"
            f" {source_string[spos:spos+50]}"
        )
