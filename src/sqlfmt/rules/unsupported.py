from functools import partial

from sqlfmt import actions
from sqlfmt.rule import Rule
from sqlfmt.rules.common import NEWLINE, SQL_QUOTED_EXP, group
from sqlfmt.rules.core import ALWAYS
from sqlfmt.tokens import TokenType

UNSUPPORTED = [
    *ALWAYS,
    # quoted names need to be lexed as DATA, so they are not formatted.
    # quoted names are otherwise in ALWAYS, (so we don't lex them as comments etc.)
    # so this rule needs to have a higher priority than the quoted_name rule in
    # ALWAYS
    Rule(
        name="quoted_name_in_unsupported",
        priority=199,
        pattern=SQL_QUOTED_EXP,
        action=partial(actions.add_node_to_buffer, token_type=TokenType.DATA),
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
