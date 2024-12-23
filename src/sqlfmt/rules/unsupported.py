from functools import partial

from sqlfmt import actions
from sqlfmt.rule import Rule
from sqlfmt.rules.common import NEWLINE, group
from sqlfmt.rules.core import ALWAYS
from sqlfmt.token import TokenType

UNSUPPORTED = [
    *ALWAYS,
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
