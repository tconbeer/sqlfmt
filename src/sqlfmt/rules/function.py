from functools import partial

from sqlfmt import actions
from sqlfmt.rule import Rule
from sqlfmt.rules.common import ALTER_DROP_FUNCTION, CREATE_FUNCTION, group
from sqlfmt.rules.core import CORE
from sqlfmt.token import TokenType

FUNCTION = [
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
        priority=1200,
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
            CREATE_FUNCTION,
            ALTER_DROP_FUNCTION,
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
            # snowflake
            r"((un)?set\s+)?comment",
            r"imports",
            r"packages",
            r"handler",
            r"target_path",
            r"(not\s+)?null",
            # snowflake external functions
            r"((un)?set\s+)?"
            + group(
                r"api_integration",
                r"headers",
                r"context_headers",
                r"max_batch_rows",
                r"compression",
                r"request_translator",
                r"response_translator",
            ),
            # bq
            r"options",
            r"remote\s+with\s+connection",
            # ALTER
            r"rename\s+to",
            r"owner\s+to",
            r"set\s+schema",
            r"(no\s+)?depends\s+on\s+extension",
            r"cascade",
            r"restrict",
            # alter snowflake
            r"(un)?set\s+secure",
            # pg catchall for set
            r"(re)?set(\s+all)?",
        )
        + group(r"\W", r"$"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.UNTERM_KEYWORD),
    ),
]
