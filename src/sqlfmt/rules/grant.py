from functools import partial

from sqlfmt import actions
from sqlfmt.rule import Rule
from sqlfmt.rules.common import group
from sqlfmt.rules.core import CORE
from sqlfmt.token import TokenType

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
