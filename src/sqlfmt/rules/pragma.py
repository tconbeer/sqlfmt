from functools import partial

from sqlfmt import actions
from sqlfmt.rule import Rule
from sqlfmt.rules.common import PRAGMA_SET_CALL, group
from sqlfmt.rules.core import CORE
from sqlfmt.tokens import TokenType

# Covers simple PRAGMA, SET, and CALL statements, e.g.:
# PRAGMA database_list;
# PRAGMA storage_info('table_name');
# CALL pragma_storage_info('table_name');
# SET default_collation = 'nocase';
PRAGMA = [
    *CORE,
    Rule(
        name="unterm_keyword",
        priority=1300,
        pattern=group(PRAGMA_SET_CALL) + group(r"\W", r"$"),
        action=partial(
            actions.handle_reserved_keyword,
            action=partial(
                actions.add_node_to_buffer, token_type=TokenType.UNTERM_KEYWORD
            ),
        ),
    ),
]
