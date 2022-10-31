import re
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Callable

from sqlfmt import actions
from sqlfmt.exception import StopJinjaLexing, StopRulesetLexing
from sqlfmt.re_utils import EOL, MAYBE_WHITESPACES, NEWLINE, group
from sqlfmt.token import TokenType

if TYPE_CHECKING:
    from sqlfmt.analyzer import Analyzer


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
    action: Callable[["Analyzer", str, re.Match], None]

    def __post_init__(self) -> None:
        self.program = re.compile(
            MAYBE_WHITESPACES + self.pattern, re.IGNORECASE | re.DOTALL
        )


SQL_QUOTED_EXP = group(
    # tripled single quotes (optionally raw/bytes)
    r"(rb?|b|br)?'''.*?'''",
    # tripled double quotes
    r'(rb?|b|br)?""".*?"""',
    # possibly escaped double quotes
    r'(rb?|b|br|u&|@)?"([^"\\]*(\\.[^"\\]*|""[^"\\]*)*)"',
    # possibly escaped single quotes
    r"(rb?|b|br|u&|x)?'([^'\\]*(\\.[^'\\]*|''[^'\\]*)*)'",
    r"\$(?P<tag>\w*)\$.*?\$(?P=tag)\$",  # pg dollar-delimited strings
    # possibly escaped backtick
    r"`([^`\\]*(\\.[^`\\]*)*)`",
)
SQL_COMMENT = group(
    r"--[^\r\n]*",
    r"#[^\r\n]*",
    r"/\*[^*]*\*+(?:[^/*][^*]*\*+)*/",  # simple block comment
)

JINJA = [
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
]

CORE = [
    Rule(
        name="fmt_off",
        priority=0,
        pattern=group(r"(--|#) ?fmt: ?off ?") + EOL,
        action=partial(actions.add_node_to_buffer, token_type=TokenType.FMT_OFF),
    ),
    Rule(
        name="fmt_on",
        priority=1,
        pattern=group(r"(--|#) ?fmt: ?on ?") + EOL,
        action=partial(actions.add_node_to_buffer, token_type=TokenType.FMT_ON),
    ),
    # These match just the start of jinja tags, which allows
    # the parser to deal with nesting in a more powerful way than
    # regex allows
    Rule(
        name="jinja_start",
        priority=120,
        pattern=group(r"\{[{%#]"),
        action=partial(
            actions.lex_ruleset, new_ruleset=JINJA, stop_exception=StopJinjaLexing
        ),
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
        pattern=SQL_QUOTED_EXP,
        action=partial(actions.add_node_to_buffer, token_type=TokenType.QUOTED_NAME),
    ),
    Rule(
        name="comment",
        priority=300,
        pattern=SQL_COMMENT,
        action=actions.add_comment_to_buffer,
    ),
    Rule(
        name="comment_start",
        priority=310,
        pattern=group(r"/\*"),
        action=partial(
            actions.handle_potentially_nested_tokens,
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
        name="number",
        priority=350,
        pattern=group(
            r"-?\d+\.?\d*",
            r"-?\.\d+",
        ),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.NUMBER),
    ),
    Rule(
        name="semicolon",
        priority=400,
        pattern=group(r";"),
        action=actions.handle_semicolon,
    ),
    Rule(
        name="star",
        priority=410,
        pattern=group(r"\*"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.STAR),
    ),
    Rule(
        name="double_colon",
        priority=420,
        pattern=group(r"::"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.DOUBLE_COLON),
    ),
    Rule(
        name="colon",
        priority=430,
        pattern=group(r":"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.COLON),
    ),
    Rule(
        name="comma",
        priority=440,
        pattern=group(r","),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.COMMA),
    ),
    Rule(
        name="dot",
        priority=450,
        pattern=group(r"\."),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.DOT),
    ),
    Rule(
        name="bracket_open",
        priority=500,
        pattern=group(
            r"\[",
            r"\(",
            r"\{",
            # bq usese angle brackets for type definitions for compound types
            r"(array|table|struct)\s*<",
        ),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.BRACKET_OPEN),
    ),
    Rule(
        name="bracket_close",
        priority=510,
        pattern=group(
            r"\]",
            r"\)",
            r"\}",
        ),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.BRACKET_CLOSE),
    ),
    Rule(
        name="other_identifiers",
        priority=600,
        pattern=group(
            r"@\w+",  # stages
            r"\$\d+",  # pg placeholders
            r"\$\w+",  # variables
            r"%(\([^%()]+\))?s",  # psycopg placeholders
        ),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.NAME),
    ),
    Rule(
        name="operator",
        priority=800,
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
            r"%%",  # psycopg escaped mod operator
            r">=",  # gte
            r"[+\-*/%&|^=<:#!]=?",  # singles
        ),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.OPERATOR),
    ),
    Rule(
        name="angle_bracket_close",
        priority=810,
        pattern=group(
            r">",
        ),
        action=partial(
            actions.safe_add_node_to_buffer,
            token_type=TokenType.BRACKET_CLOSE,
            fallback_token_type=TokenType.OPERATOR,
        ),
    ),
    Rule(
        name="name",
        priority=5000,
        pattern=group(r"\w+"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.NAME),
    ),
    Rule(
        name="newline",
        priority=9000,
        pattern=group(NEWLINE),
        action=actions.handle_newline,
    ),
]

GRANT = [
    *CORE,
    Rule(
        name="unterm_keyword",
        priority=1300,
        pattern=group(
            r"grant",
            r"revoke(\s+grant\s+option\s+for)?",
            r"on",
            r"to",
            r"from",
            r"with\s+grant\s+option",
            r"granted\s+by",
            r"cascade",
            r"restrict",
        )
        + group(r"\W", r"$"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.UNTERM_KEYWORD),
    ),
]

CREATE_FUNCTION = [
    *CORE,
    Rule(
        name="function_as",
        priority=1100,
        pattern=group(
            r"as",
        )
        + group(r"\W", r"$"),
        action=actions.handle_ddl_as,
    ),
    Rule(
        name="word_operator",
        priority=1100,
        pattern=group(
            r"to",
            r"from",
            # snowflake
            r"runtime_version",
        )
        + group(r"\W", r"$"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.WORD_OPERATOR),
    ),
    Rule(
        name="unterm_keyword",
        priority=1300,
        pattern=group(
            (
                r"create(\s+or\s+replace)?(\s+temp(orary)?)?(\s+secure)?(\s+table)?"
                r"\s+function(\s+if\s+not\s+exists)?"
            ),
            r"language",
            r"transform",
            r"immutable",
            r"stable",
            r"volatile",
            r"(not\s+)?leakproof",
            r"volatile",
            r"called\s+on\s+null\s+input",
            r"returns\s+null\s+on\s+null\s+input",
            r"return(s)?(?!\s+null)",
            r"strict",
            r"(external\s+)?security\s+(invoker|definer)",
            r"parallel\s+(unsafe|restricted|safe)",
            r"cost",
            r"rows",
            r"support",
            r"set",
            r"as",
            # snowflake
            r"comment",
            r"imports",
            r"packages",
            r"handler",
            r"target_path",
            r"(not\s+)?null",
            # bq
            r"options",
            r"remote\s+with\s+connection",
        )
        + group(r"\W", r"$"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.UNTERM_KEYWORD),
    ),
]

MAIN = [
    *CORE,
    Rule(
        name="statement_start",
        priority=1000,
        pattern=group(r"case") + group(r"\W", r"$"),
        action=partial(
            actions.add_node_to_buffer, token_type=TokenType.STATEMENT_START
        ),
    ),
    Rule(
        name="statement_end",
        priority=1010,
        pattern=group(r"end") + group(r"\W", r"$"),
        action=partial(
            actions.safe_add_node_to_buffer,
            token_type=TokenType.STATEMENT_END,
            fallback_token_type=TokenType.NAME,
        ),
    ),
    Rule(
        name="word_operator",
        priority=1100,
        pattern=group(
            r"all",
            r"any",
            r"as",
            r"(not\s+)?between",
            r"cube",
            r"(not\s+)?exists",
            r"filter",
            r"grouping sets",
            r"(not\s+)?in",
            r"is(\s+not)?",
            r"isnull",
            r"(not\s+)?i?like(\s+any)?",
            r"over",
            r"(un)?pivot",
            r"notnull",
            r"(not\s+)?regexp",
            r"(not\s+)?rlike",
            r"rollup",
            r"some",
            r"(not\s+)?similar\s+to",
            r"tablesample",
            r"within\s+group",
        )
        + group(r"\W", r"$"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.WORD_OPERATOR),
    ),
    Rule(
        name="star_replace_exclude",
        priority=1101,
        pattern=group(
            r"exclude",
            r"replace",
        )
        + group(r"\s+\("),
        action=partial(
            actions.add_node_to_buffer,
            token_type=TokenType.WORD_OPERATOR,
        ),
    ),
    Rule(
        # a join's using word operator must be followed
        # by parens; otherwise, it's probably a
        # delete's USING, which is an unterminated
        # keyword
        name="join_using",
        priority=1110,
        pattern=group(r"using") + group(r"\s*\("),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.WORD_OPERATOR),
    ),
    Rule(
        name="on",
        priority=1120,
        pattern=group(r"on") + group(r"\W", r"$"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.ON),
    ),
    Rule(
        name="boolean_operator",
        priority=1200,
        pattern=group(
            r"and",
            r"or",
            r"not",
        )
        + group(r"\W", r"$"),
        action=partial(
            actions.add_node_to_buffer,
            token_type=TokenType.BOOLEAN_OPERATOR,
        ),
    ),
    Rule(
        name="unterm_keyword",
        priority=1300,
        pattern=group(
            r"with(\s+recursive)?",
            (
                r"select(\s+(as\s+struct|as\s+value))?"
                r"(\s+(all|top\s+\d+|distinct))?"
                # select into is ddl that needs additional handling
                r"(?!\s+into)"
            ),
            r"delete\s+from",
            r"from",
            (
                r"(natural\s+)?"
                r"((inner|cross|((left|right|full)(\s+outer)?))\s+)?join"
            ),
            # this is the USING following DELETE, not the join operator
            # (see above)
            r"using",
            r"lateral\s+view(\s+outer)?",
            r"where",
            r"group\s+by",
            r"cluster\s+by",
            r"distribute\s+by",
            r"sort\s+by",
            r"having",
            r"qualify",
            r"window",
            r"order\s+by",
            r"limit",
            r"fetch\s+(first|next)",
            r"for\s+(update|no\s+key\s+update|share|key\s+share)",
            r"when",
            r"then",
            r"else",
            r"partition\s+by",
            r"rows\s+between",
            r"values",
            # in pg, RETURNING can be the last clause of
            # a DELETE statement
            r"returning",
        )
        + group(r"\W", r"$"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.UNTERM_KEYWORD),
    ),
    Rule(
        # BQ arrays use an offset(n) function for
        # indexing that we do not want to match. This
        # should only match the offset in limit ... offset,
        # which must be followed by a space
        name="offset_keyword",
        priority=1310,
        pattern=group(r"offset") + group(r"\s+", r"$"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.UNTERM_KEYWORD),
    ),
    Rule(
        name="set_operator",
        priority=1320,
        pattern=group(
            r"(union|intersect|except|minus)(\s+all|distinct)?",
        )
        + group(r"\W", r"$"),
        action=actions.handle_set_operator,
    ),
    Rule(
        name="explain",
        priority=2000,
        pattern=group(r"explain(\s+(analyze|verbose|using\s+(tabular|json|text)))?")
        + group(r"\W", r"$"),
        action=partial(
            actions.handle_nonreserved_keyword,
            action=partial(
                actions.add_node_to_buffer, token_type=TokenType.UNTERM_KEYWORD
            ),
        ),
    ),
    Rule(
        name="grant",
        priority=2010,
        pattern=group(r"grant", r"revoke") + group(r"\W", r"$"),
        action=partial(
            actions.handle_nonreserved_keyword,
            action=partial(
                actions.lex_ruleset, new_ruleset=GRANT, stop_exception=StopRulesetLexing
            ),
        ),
    ),
    Rule(
        name="create_function",
        priority=2020,
        pattern=group(
            (
                r"create(\s+or\s+replace)?(\s+temp(orary)?)?(\s+secure)?(\s+table)?"
                r"\s+function(\s+if\s+not\s+exists)?"
            ),
        )
        + group(r"\W", r"$"),
        action=partial(
            actions.handle_nonreserved_keyword,
            action=partial(
                actions.lex_ruleset,
                new_ruleset=CREATE_FUNCTION,
                stop_exception=StopRulesetLexing,
            ),
        ),
    ),
    Rule(
        name="unsupported_ddl",
        priority=2999,
        pattern=group(
            group(
                r"alter",
                r"attach\s+rls\s+policy",
                r"cache\s+table",
                r"clear\s+cache",
                r"cluster",
                r"comment",
                r"copy",
                r"create",
                r"deallocate",
                r"declare",
                r"describe",
                r"desc\s+datashare",
                r"desc\s+identity\s+provider",
                r"delete",
                r"detach\s+rls\s+policy",
                r"discard",
                r"do",
                r"drop",
                r"execute",
                r"export",
                r"fetch",
                r"get",
                r"handler",
                r"import\s+foreign\s+schema",
                r"import\s+table",
                # snowflake: "insert into" or "insert overwrite into"
                # snowflake: has insert() function
                # spark: "insert overwrite" without the trailing "into"
                # redshift/pg: "insert into" only
                # bigquery: bare "insert" is okay
                r"insert(\s+overwrite)?(\s+into)?(?!\()",
                r"list",
                r"lock",
                r"merge",
                r"move",
                # prepare transaction statements are simple enough
                # so we'll allow them
                r"prepare(?!\s+transaction)",
                r"put",
                r"reassign\s+owned",
                r"remove",
                r"rename\s+table",
                r"repair",
                r"security\s+label",
                r"select\s+into",
                r"truncate",
                r"unload",
                r"update",
                r"validate",
            )
            + rf"\b({SQL_COMMENT}|{SQL_QUOTED_EXP}|[^'`\"$;])*?"
        )
        + rf"{NEWLINE}*"
        + group(r";", r"$"),
        action=actions.handle_possible_unsupported_ddl,
    ),
]
