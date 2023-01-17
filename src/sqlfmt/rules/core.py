from functools import partial

from sqlfmt import actions
from sqlfmt.rule import Rule
from sqlfmt.rules.common import EOL, NEWLINE, SQL_COMMENT, SQL_QUOTED_EXP, group
from sqlfmt.rules.jinja import JINJA
from sqlfmt.token import TokenType

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
        action=partial(actions.lex_ruleset, new_ruleset=JINJA),
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
            r"(\+|-)?\d+(\.\d*)?(e(\+|-)?\d+)?",
            r"(\+|-)?\.\d+(e(\+|-)?\d+)?",
        ),
        action=actions.handle_number,
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
            r"\?\d+",  # bun placeholders
        ),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.NAME),
    ),
    Rule(
        name="angle_bracket_close",
        priority=790,
        pattern=group(
            r">",
        ),
        action=actions.handle_closing_angle_bracket,
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
            r"[+\-*/%&|^=<>:#!]=?",  # singles
        ),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.OPERATOR),
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
