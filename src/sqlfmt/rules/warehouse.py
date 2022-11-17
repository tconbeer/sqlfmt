from functools import partial

from sqlfmt import actions
from sqlfmt.rule import Rule
from sqlfmt.rules.common import ALTER_WAREHOUSE, CREATE_WAREHOUSE, group
from sqlfmt.rules.core import CORE
from sqlfmt.token import TokenType

WAREHOUSE = [
    *CORE,
    Rule(
        name="unterm_keyword",
        priority=1300,
        pattern=group(
            CREATE_WAREHOUSE,
            ALTER_WAREHOUSE,
            # objectProperties
            r"(with\s+|(un)?set\s+)?"
            + group(
                r"warehouse_type",
                r"warehouse_size",
                r"max_cluster_count",
                r"min_cluster_count",
                r"scaling_policy",
                r"auto_suspend",
                r"auto_resume",
                r"initially_suspended",
                r"resource_monitor",
                r"comment",
                r"enable_query_acceleration",
                r"query_acceleration_max_scale_factor",
                r"tag",
            ),
            # objectParams
            r"(set\s+)?"
            + group(
                r"max_concurrency_level",
                r"statement_queued_timeout_in_seconds",
                r"statement_timeout_in_seconds",
            ),
            # alter
            r"suspend",
            r"resume(\s+if\s+suspended)?",
            r"abort\s+all\s+queries",
            r"rename\s+to",
        )
        + group(r"\W", r"$"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.UNTERM_KEYWORD),
    ),
]
