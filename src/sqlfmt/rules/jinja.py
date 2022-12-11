from functools import partial

from sqlfmt import actions
from sqlfmt.rule import Rule
from sqlfmt.rules.common import NEWLINE, group
from sqlfmt.token import TokenType

JINJA_SHARED_PATTERNS = {
    "set": r"\{%-?\s*set\s+[^=]+?-?%\}",
    "endset": r"\{%-?\s*endset\s*-?%\}",
    "call": r"\{%-?\s*call\s+\w+.*?-?%\}",
    "endcall": r"\{%-?\s*endcall\s*-?%\}",
}

JINJA_DATA = [
    Rule(
        name="jinja_set_block_start",
        priority=100,
        pattern=group(JINJA_SHARED_PATTERNS["set"]),
        action=partial(
            actions.handle_jinja_data_block_start,
            new_ruleset=None,
            raises=False,
        ),
    ),
    Rule(
        name="jinja_set_block_end",
        priority=101,
        pattern=group(JINJA_SHARED_PATTERNS["endset"]),
        action=partial(
            actions.handle_jinja_block_end,
            start_rule_names=["jinja_set_block_start"],
            reset_sql_depth=True,
        ),
    ),
    Rule(
        name="jinja_call_block_start",
        priority=261,
        pattern=group(JINJA_SHARED_PATTERNS["call"]),
        action=partial(
            actions.handle_jinja_data_block_start,
            new_ruleset=None,
            raises=False,
        ),
    ),
    Rule(
        name="jinja_call_block_end",
        priority=265,
        pattern=group(JINJA_SHARED_PATTERNS["endcall"]),
        action=partial(
            actions.handle_jinja_block_end,
            start_rule_names=["jinja_call_block_start"],
            reset_sql_depth=True,
        ),
    ),
    Rule(
        name="jinja_newline",
        priority=500,
        pattern=group(NEWLINE),
        action=actions.handle_newline,
    ),
    Rule(
        name="jinja_data",
        priority=600,
        pattern=group(r".*?") + r"\s*" + group(*JINJA_SHARED_PATTERNS.values(), r"$"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.DATA),
    ),
]

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
        pattern=group(JINJA_SHARED_PATTERNS["set"]),
        action=partial(
            actions.handle_jinja_data_block_start,
            new_ruleset=JINJA_DATA,
        ),
    ),
    Rule(
        name="jinja_set_block_end",
        priority=101,
        pattern=group(JINJA_SHARED_PATTERNS["endset"]),
        action=actions.raise_sqlfmt_bracket_error,
    ),
    Rule(
        name="jinja_if_block_start",
        priority=200,
        pattern=group(r"\{%-?\s*if.*?-?%\}"),
        action=actions.handle_jinja_block_start,
    ),
    Rule(
        name="jinja_elif_block_start",
        priority=201,
        pattern=group(r"\{%-?\s*elif\s+\w+.*?-?%\}"),
        action=partial(
            actions.handle_jinja_block_keyword,
            start_rule_names=[
                "jinja_if_block_start",
                "jinja_elif_block_start",
                "jinja_else_block_start",
            ],
        ),
    ),
    Rule(
        name="jinja_else_block_start",
        priority=202,
        pattern=group(r"\{%-?\s*else\s*-?%\}"),
        action=partial(
            actions.handle_jinja_block_keyword,
            start_rule_names=[
                "jinja_if_block_start",
                "jinja_elif_block_start",
                "jinja_else_block_start",
            ],
        ),
    ),
    Rule(
        name="jinja_if_block_end",
        priority=203,
        pattern=group(r"\{%-?\s*endif\s*-?%\}"),
        action=partial(
            actions.handle_jinja_block_end,
            start_rule_names=[
                "jinja_if_block_start",
                "jinja_elif_block_start",
                "jinja_else_block_start",
            ],
        ),
    ),
    Rule(
        name="jinja_for_block_start",
        priority=210,
        pattern=group(r"\{%-?\s*for\s+.*?-?%\}"),
        action=actions.handle_jinja_block_start,
    ),
    Rule(
        name="jinja_for_block_end",
        priority=211,
        pattern=group(r"\{%-?\s*endfor\s*-?%\}"),
        action=partial(
            actions.handle_jinja_block_end, start_rule_names=["jinja_for_block_start"]
        ),
    ),
    Rule(
        name="jinja_macro_block_start",
        priority=220,
        pattern=group(r"\{%-?\s*macro\s+\w+.*?-?%\}"),
        action=actions.handle_jinja_block_start,
    ),
    Rule(
        name="jinja_macro_block_end",
        priority=221,
        pattern=group(r"\{%-?\s*endmacro\s*-?%\}"),
        action=partial(
            actions.handle_jinja_block_end,
            start_rule_names=["jinja_macro_block_start"],
            reset_sql_depth=True,
        ),
    ),
    Rule(
        name="jinja_test_block_start",
        priority=230,
        pattern=group(r"\{%-?\s*test\s+\w+.*?-?%\}"),
        action=actions.handle_jinja_block_start,
    ),
    Rule(
        name="jinja_test_block_end",
        priority=231,
        pattern=group(r"\{%-?\s*endtest\s*-?%\}"),
        action=partial(
            actions.handle_jinja_block_end,
            start_rule_names=["jinja_test_block_start"],
            reset_sql_depth=True,
        ),
    ),
    Rule(
        name="jinja_snapshot_block_start",
        priority=240,
        pattern=group(r"\{%-?\s*snapshot\s+\w+.*?-?%\}"),
        action=actions.handle_jinja_block_start,
    ),
    Rule(
        name="jinja_snapshot_block_end",
        priority=241,
        pattern=group(r"\{%-?\s*endsnapshot\s*-?%\}"),
        action=partial(
            actions.handle_jinja_block_end,
            start_rule_names=["jinja_snapshot_block_start"],
            reset_sql_depth=True,
        ),
    ),
    Rule(
        name="jinja_materialization_block_start",
        priority=250,
        pattern=group(r"\{%-?\s*materialization\s+\w+\s*,.*?-?%\}"),
        action=actions.handle_jinja_block_start,
    ),
    Rule(
        name="jinja_materialization_block_end",
        priority=251,
        pattern=group(r"\{%-?\s*endmaterialization\s*-?%\}"),
        action=partial(
            actions.handle_jinja_block_end,
            start_rule_names=["jinja_materialization_block_start"],
            reset_sql_depth=True,
        ),
    ),
    # call blocks that are used to call dbt's statement macro
    # are guaranteed to contain SQL, so we can parse them
    # like ordinary jinja blocks, and format the contents
    Rule(
        name="jinja_call_statement_block_start",
        priority=260,
        pattern=group(r"\{%-?\s*call\s+(noop_)?statement\(.*?\)\s*-?%\}"),
        action=actions.handle_jinja_block_start,
    ),
    # call blocks that call other macros may contain SQL or
    # arbitrary text or data, so we need to parse the whole block
    # as DATA so we don't format it
    Rule(
        name="jinja_call_block_start",
        priority=261,
        pattern=group(JINJA_SHARED_PATTERNS["call"]),
        action=partial(
            actions.handle_jinja_data_block_start,
            new_ruleset=JINJA_DATA,
        ),
    ),
    Rule(
        name="jinja_call_block_end",
        priority=265,
        pattern=group(JINJA_SHARED_PATTERNS["endcall"]),
        action=partial(
            actions.handle_jinja_block_end,
            start_rule_names=["jinja_call_statement_block_start"],
            reset_sql_depth=True,
        ),
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
