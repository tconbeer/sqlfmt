from functools import partial

from sqlfmt import actions
from sqlfmt.rule import Rule
from sqlfmt.rules.common import NEWLINE, SQL_COMMENT, SQL_QUOTED_EXP, group
from sqlfmt.rules.jinja import JINJA
from sqlfmt.token import TokenType

UNSUPPORTED = [
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
        name="semicolon",
        priority=400,
        pattern=group(r";"),
        action=actions.handle_semicolon,
    ),
    Rule(
        name="newline",
        priority=999,
        pattern=group(NEWLINE),
        action=actions.handle_newline,
    ),
    Rule(
        name="unsupported_line",
        priority=1000,
        pattern=group(r"[^;\n]+?") + group(r";", NEWLINE, r"$"),
        action=partial(
            actions.handle_reserved_keyword,
            action=partial(actions.add_node_to_buffer, token_type=TokenType.DATA),
        ),
    ),
]
