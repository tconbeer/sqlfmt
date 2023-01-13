from functools import partial

from sqlfmt import actions
from sqlfmt.rule import Rule
from sqlfmt.rules.common import CREATE_CLONABLE, group
from sqlfmt.rules.core import CORE
from sqlfmt.token import TokenType

CLONE = [
    *CORE,
    Rule(
        name="unterm_keyword",
        priority=1300,
        pattern=group(CREATE_CLONABLE, r"clone") + group(r"\W", r"$"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.UNTERM_KEYWORD),
    ),
    Rule(
        name="word_operator",
        priority=1500,
        pattern=group(
            r"at",
            r"before",
        )
        + group(r"\W", r"$"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.WORD_OPERATOR),
    ),
]
