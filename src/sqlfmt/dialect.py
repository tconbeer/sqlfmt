from abc import ABC, abstractmethod
from functools import partial
from typing import Dict, List

from sqlfmt.analyzer import Analyzer, Rule, group
from sqlfmt.token import TokenType

NEWLINE: str = r"\r?\n"
EOL = group(NEWLINE, r"$")


class Dialect(ABC):
    """
    Abstract class for a SQL dialect.

    Each dialect should override the RULES dict to define their own grammar. RULES
    must have a key "main" that contains the rules for the main lexing loop.
    """

    RULES: Dict[str, List[Rule]]

    @abstractmethod
    def get_rules(self) -> Dict[str, List[Rule]]:
        """
        Returns the Dialect's Rules, as a dict keyed by the name of the ruleset,
        e.g., main
        """
        return {
            k: sorted(v, key=lambda rule: rule.priority) for k, v in self.RULES.items()
        }

    def initialize_analyzer(self, line_length: int) -> Analyzer:
        """
        Creates and returns an analyzer that uses the Dialect's rules for lexing
        """
        analyzer = Analyzer(
            line_length=line_length,
            rules=self.get_rules(),
        )
        return analyzer


class Polyglot(Dialect):
    """
    A universal SQL dialect meant to encompass the common usage of at least
    Postgres, MySQL, BigQuery Standard SQL, Snowflake SQL, SparkSQL.
    """

    def __init__(self) -> None:
        from sqlfmt import actions

        self.RULES: Dict[str, List[Rule]] = {
            "main": [
                Rule(
                    name="fmt_off",
                    priority=0,
                    pattern=group(r"(--|#) ?fmt: ?off ?") + EOL,
                    action=partial(
                        actions.add_node_to_buffer, token_type=TokenType.FMT_OFF
                    ),
                ),
                Rule(
                    name="fmt_on",
                    priority=1,
                    pattern=group(r"(--|#) ?fmt: ?on ?") + EOL,
                    action=partial(
                        actions.add_node_to_buffer, token_type=TokenType.FMT_ON
                    ),
                ),
                # These match just the start of jinja tags, which allows
                # the parser to deal with nesting in a more powerful way than
                # regex allows
                Rule(
                    name="jinja_start",
                    priority=120,
                    pattern=group(r"\{[{%#]"),
                    action=actions.lex_jinja,
                ),
                # we should never match the end of a jinja tag by itself
                Rule(
                    name="jinja_end",
                    priority=130,
                    pattern=group(r"[#}%]\}"),
                    action=actions.raise_sqlfmt_bracket_error,
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
                        r'(rb?|b|br|u&|@)?"([^"\\]*(\\.[^"\\]*|""[^"\\]*)*)"',
                        # possibly escaped single quotes
                        r"(rb?|b|br|u&|x)?'([^'\\]*(\\.[^'\\]*|''[^'\\]*)*)'",
                        r"\$\w*\$[^$]*?\$\w*\$",  # pg dollar-delimited strings
                        # possibly escaped backtick
                        r"`([^`\\]*(\\.[^`\\]*)*)`",
                    ),
                    action=partial(
                        actions.add_node_to_buffer, token_type=TokenType.QUOTED_NAME
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
                    action=actions.add_comment_to_buffer,
                ),
                Rule(
                    name="comment_start",
                    priority=310,
                    pattern=group(r"/\*"),
                    action=partial(
                        actions.handle_potentially_nested_tokens,
                        ruleset="main",
                        start_name="comment_start",
                        end_name="comment_end",
                        token_type=TokenType.COMMENT,
                    ),
                ),
                Rule(
                    name="comment_end",
                    priority=320,
                    pattern=group(r"\*/"),
                    action=actions.raise_sqlfmt_bracket_error,
                ),
                Rule(
                    name="semicolon",
                    priority=400,
                    pattern=group(r";"),
                    action=partial(
                        actions.add_node_to_buffer, token_type=TokenType.SEMICOLON
                    ),
                ),
                Rule(
                    name="statement_start",
                    priority=500,
                    pattern=group(r"case") + group(r"\W", r"$"),
                    action=partial(
                        actions.add_node_to_buffer, token_type=TokenType.STATEMENT_START
                    ),
                ),
                Rule(
                    name="statement_end",
                    priority=510,
                    pattern=group(r"end") + group(r"\W", r"$"),
                    action=partial(
                        actions.safe_add_node_to_buffer,
                        token_type=TokenType.STATEMENT_END,
                        fallback_token_type=TokenType.NAME,
                    ),
                ),
                Rule(
                    name="star",
                    priority=600,
                    pattern=group(r"\*"),
                    action=partial(
                        actions.add_node_to_buffer, token_type=TokenType.STAR
                    ),
                ),
                Rule(
                    name="number",
                    priority=700,
                    pattern=group(
                        r"-?\d+\.?\d*",
                        r"-?\.\d+",
                    ),
                    action=partial(
                        actions.add_node_to_buffer, token_type=TokenType.NUMBER
                    ),
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
                        actions.add_node_to_buffer, token_type=TokenType.BRACKET_OPEN
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
                        actions.add_node_to_buffer, token_type=TokenType.BRACKET_CLOSE
                    ),
                ),
                Rule(
                    name="double_colon",
                    priority=900,
                    pattern=group(r"::"),
                    action=partial(
                        actions.add_node_to_buffer, token_type=TokenType.DOUBLE_COLON
                    ),
                ),
                Rule(
                    name="colon",
                    priority=905,
                    pattern=group(r":"),
                    action=partial(
                        actions.add_node_to_buffer, token_type=TokenType.COLON
                    ),
                ),
                Rule(
                    name="operator",
                    priority=910,
                    pattern=group(
                        r"\|\|?\/",  # square or cube root ||/
                        r"~=",  # geo compare
                        r"!?~\*?",  # posix like/not like
                        r"\?(=|!|<=|<!)",  # regex lookahead/behind
                        r"\?(-\||\|\||-|\|)",  # regex lookahead/behind
                        r"@-@",  # length operator
                        r"@@@?",  # center point operator; also text match
                        r"##",  # closest point
                        r"<->",  # distance operator
                        r"@>",  # contains
                        r"<@",  # contained by
                        r"<>",
                        r"\|?>>=?",
                        r"<<(=|\|)?",
                        r"=>",
                        r"(-|#)>>?",  # json extraction
                        r"&&",
                        r"&<\|?",  # not extends
                        r"\|?&>",  # not extends
                        r"<\^",  # below
                        r">\^",  # above
                        r"\?#",  # intersect
                        r"\|\|",
                        r"-\|-",
                        r"[*+?]?\?",  # regex greedy/non-greedy, also ?
                        r"!!",  # negate text match
                        r"[+\-*/%&|^=<>:#!]=?",  # singles
                    ),
                    action=partial(
                        actions.add_node_to_buffer, token_type=TokenType.OPERATOR
                    ),
                ),
                Rule(
                    name="word_operator",
                    priority=920,
                    pattern=group(
                        r"all",
                        r"any",
                        r"between",
                        r"cube",
                        r"exists",
                        r"grouping sets",
                        r"ilike",
                        r"in",
                        r"is",
                        r"isnull",
                        r"like(\s+any)?",
                        r"notnull",
                        r"not",
                        r"over",
                        r"rollup",
                        r"rlike",
                        r"some",
                        r"similar\s+to",
                    )
                    + group(r"\W", r"$"),
                    action=partial(
                        actions.add_node_to_buffer, token_type=TokenType.WORD_OPERATOR
                    ),
                ),
                Rule(
                    name="as",
                    priority=930,
                    pattern=group(r"as") + group(r"\W", r"$"),
                    action=partial(actions.add_node_to_buffer, token_type=TokenType.AS),
                ),
                Rule(
                    name="on",
                    priority=940,
                    pattern=group(r"on") + group(r"\W", r"$"),
                    action=partial(actions.add_node_to_buffer, token_type=TokenType.ON),
                ),
                Rule(
                    name="boolean_operator",
                    priority=950,
                    pattern=group(
                        r"and",
                        r"or",
                    )
                    + group(r"\W", r"$"),
                    action=partial(
                        actions.add_node_to_buffer,
                        token_type=TokenType.BOOLEAN_OPERATOR,
                    ),
                ),
                Rule(
                    name="comma",
                    priority=960,
                    pattern=group(r","),
                    action=partial(
                        actions.add_node_to_buffer, token_type=TokenType.COMMA
                    ),
                ),
                Rule(
                    name="dot",
                    priority=970,
                    pattern=group(r"\."),
                    action=partial(
                        actions.add_node_to_buffer, token_type=TokenType.DOT
                    ),
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
                        (
                            r"(natural\s+)?"
                            r"((inner|cross|((left|right|full)(\s+outer)?))\s+)?join"
                        ),
                        r"where",
                        r"group\s+by",
                        r"having",
                        r"qualify",
                        r"window",
                        r"(union|intersect|except|minus)(\s+all|distinct)?",
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
                        actions.add_node_to_buffer, token_type=TokenType.UNTERM_KEYWORD
                    ),
                ),
                Rule(
                    name="other_identifiers",
                    priority=4000,
                    pattern=group(r"@\w+", r"\$\d+"),
                    action=partial(
                        actions.add_node_to_buffer, token_type=TokenType.NAME
                    ),
                ),
                Rule(
                    name="name",
                    priority=5000,
                    pattern=group(r"\w+"),
                    action=partial(
                        actions.add_node_to_buffer, token_type=TokenType.NAME
                    ),
                ),
                Rule(
                    name="newline",
                    priority=9000,
                    pattern=group(NEWLINE),
                    action=actions.handle_newline,
                ),
            ],
            "jinja": [
                Rule(
                    name="jinja_comment",
                    priority=0,
                    pattern=group(r"\{\#.*?\#\}"),
                    action=actions.add_jinja_comment_to_buffer,
                ),
                Rule(
                    name="jinja_set_block_start",
                    priority=100,
                    pattern=group(r"\{%-?\s*set\s+[^=]+?-?%\}"),
                    action=actions.handle_jinja_set_block,
                ),
                Rule(
                    name="jinja_set_block_end",
                    priority=101,
                    pattern=group(r"\{%-?\s*endset\s*-?%\}"),
                    action=actions.raise_sqlfmt_bracket_error,
                ),
                Rule(
                    name="jinja_if_block_start",
                    priority=200,
                    pattern=group(r"\{%-?\s*if.*?-?%\}"),
                    action=partial(
                        actions.handle_jinja_block,
                        start_name="jinja_if_block_start",
                        end_name="jinja_if_block_end",
                        other_names=[
                            "jinja_elif_block_start",
                            "jinja_else_block_start",
                        ],
                    ),
                ),
                Rule(
                    name="jinja_elif_block_start",
                    priority=201,
                    pattern=group(r"\{%-?\s*elif\s+\w+.*?-?%\}"),
                    action=actions.raise_sqlfmt_bracket_error,
                ),
                Rule(
                    name="jinja_else_block_start",
                    priority=202,
                    pattern=group(r"\{%-?\s*else\s*-?%\}"),
                    action=actions.raise_sqlfmt_bracket_error,
                ),
                Rule(
                    name="jinja_if_block_end",
                    priority=203,
                    pattern=group(r"\{%-?\s*endif\s*-?%\}"),
                    action=actions.raise_sqlfmt_bracket_error,
                ),
                Rule(
                    name="jinja_for_block_start",
                    priority=210,
                    pattern=group(r"\{%-?\s*for\s+.*?-?%\}"),
                    action=partial(
                        actions.handle_jinja_block,
                        start_name="jinja_for_block_start",
                        end_name="jinja_for_block_end",
                        other_names=[],
                    ),
                ),
                Rule(
                    name="jinja_for_block_end",
                    priority=211,
                    pattern=group(r"\{%-?\s*endfor\s*-?%\}"),
                    action=actions.raise_sqlfmt_bracket_error,
                ),
                Rule(
                    name="jinja_macro_block_start",
                    priority=220,
                    pattern=group(r"\{%-?\s*macro\s+\w+.*?-?%\}"),
                    action=partial(
                        actions.handle_jinja_block,
                        start_name="jinja_macro_block_start",
                        end_name="jinja_macro_block_end",
                        other_names=[],
                    ),
                ),
                Rule(
                    name="jinja_macro_block_end",
                    priority=221,
                    pattern=group(r"\{%-?\s*endmacro\s*-?%\}"),
                    action=actions.raise_sqlfmt_bracket_error,
                ),
                Rule(
                    name="jinja_test_block_start",
                    priority=230,
                    pattern=group(r"\{%-?\s*test\s+\w+.*?-?%\}"),
                    action=partial(
                        actions.handle_jinja_block,
                        start_name="jinja_test_block_start",
                        end_name="jinja_test_block_end",
                        other_names=[],
                    ),
                ),
                Rule(
                    name="jinja_test_block_end",
                    priority=231,
                    pattern=group(r"\{%-?\s*endtest\s*-?%\}"),
                    action=actions.raise_sqlfmt_bracket_error,
                ),
                Rule(
                    name="jinja_snapshot_block_start",
                    priority=240,
                    pattern=group(r"\{%-?\s*snapshot\s+\w+.*?-?%\}"),
                    action=partial(
                        actions.handle_jinja_block,
                        start_name="jinja_snapshot_block_start",
                        end_name="jinja_snapshot_block_end",
                        other_names=[],
                    ),
                ),
                Rule(
                    name="jinja_snapshot_block_end",
                    priority=241,
                    pattern=group(r"\{%-?\s*endsnapshot\s*-?%\}"),
                    action=actions.raise_sqlfmt_bracket_error,
                ),
                Rule(
                    name="jinja_statement_start",
                    priority=500,
                    pattern=group(r"\{%-?"),
                    action=partial(
                        actions.handle_jinja,
                        start_name="jinja_statement_start",
                        end_name="jinja_statement_end",
                        token_type=TokenType.JINJA_STATEMENT,
                    ),
                ),
                Rule(
                    name="jinja_expression_start",
                    priority=510,
                    pattern=group(r"\{\{-?"),
                    action=partial(
                        actions.handle_jinja,
                        start_name="jinja_expression_start",
                        end_name="jinja_expression_end",
                        token_type=TokenType.JINJA_EXPRESSION,
                    ),
                ),
                Rule(
                    name="jinja_statement_end",
                    priority=600,
                    pattern=group(r"-?%\}"),
                    action=actions.raise_sqlfmt_bracket_error,
                ),
                Rule(
                    name="jinja_expression_end",
                    priority=610,
                    pattern=group(r"-?\}\}"),
                    action=actions.raise_sqlfmt_bracket_error,
                ),
            ],
        }

    def get_rules(self) -> Dict[str, List[Rule]]:
        return super().get_rules()
